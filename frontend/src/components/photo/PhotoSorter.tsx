'use client';
import {useState} from 'react';
import {Photo} from '@/types';
import {api, frameNumber, json, message} from '@/lib/api';
import {FilmFrame} from '@/components/film/FilmFrame';
import {ErrorNotice} from '@/components/layout/Feedback';
import {Modal} from '@/components/layout/Modal';
export function PhotoSorter({rollId, photos, changed}: {rollId: number; photos: Photo[]; changed: () => Promise<void>}) {
  const [dragged, setDragged] = useState<number | null>(null), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [editing, setEditing] = useState<Photo | null>(null), [caption, setCaption] = useState('');
  async function mutate(path: string, method: string, data?: unknown) {
    if (busy) return;
    setBusy(true); setError('');
    try {await api(path, json(method, data)); await changed(); setEditing(null);} catch (err) {setError(message(err));} finally {setBusy(false);}
  }
  async function move(from: number, to: number) {
    if (busy || to < 0 || to >= photos.length || from === to) return;
    const ids = photos.map(p => p.id), source = ids.splice(from, 1)[0]; ids.splice(to, 0, source);
    await mutate(`/rolls/${rollId}/photos/reorder`, 'PUT', {photo_ids: ids});
  }
  return <><div className="section-heading"><h3>照片顺序</h3><span className="muted">拖动排序，或用前移 / 后移按钮</span></div><ErrorNotice error={error}/><div className="photo-sorter" aria-busy={busy}>{photos.map((photo, index) => <div key={photo.id} className={`sort-item ${dragged === index ? 'dragging' : ''}`} draggable={!busy && !editing} onDragStart={e => {setDragged(index); e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', String(index));}} onDragEnd={() => setDragged(null)} onDragOver={e => e.preventDefault()} onDrop={e => {e.preventDefault(); if (dragged !== null) void move(dragged, index); setDragged(null);}}><FilmFrame photo={photo} variant="thumbnail"/><div className="sort-heading"><span className="mono">{frameNumber(photo.frame_number)}</span><span>{photo.is_cover ? '封面' : ''}{photo.is_favorite ? ' ★' : ''}</span></div><p className="file-name" title={photo.original_filename}>{photo.original_filename}</p><div className="photo-actions"><button disabled={busy || index === 0} onClick={() => void move(index, index - 1)} aria-label={`前移第 ${photo.frame_number} 张`}>←</button><button disabled={busy || index === photos.length - 1} onClick={() => void move(index, index + 1)} aria-label={`后移第 ${photo.frame_number} 张`}>→</button><button disabled={busy || photo.is_cover} onClick={() => void mutate(`/rolls/${rollId}/cover/${photo.id}`, 'PUT')}>设封面</button><button disabled={busy} aria-pressed={photo.is_favorite} onClick={() => void mutate(`/photos/${photo.id}`, 'PUT', {is_favorite: !photo.is_favorite})}>{photo.is_favorite ? '取消收藏' : '收藏'}</button><button disabled={busy} onClick={() => {setEditing(photo); setCaption(photo.caption);}}>图注</button><button disabled={busy} className="danger-text" onClick={() => {if (confirm(`删除第 ${photo.frame_number} 张照片？图片文件将一并删除。`)) void mutate(`/photos/${photo.id}`, 'DELETE');}}>删除</button></div></div>)}</div>{editing && <Modal title={`第 ${editing.frame_number} 张 · 图注`} close={() => {if (!busy) setEditing(null);}}><form onSubmit={e => {e.preventDefault(); void mutate(`/photos/${editing.id}`, 'PUT', {caption});}}><label>照片说明<textarea autoFocus rows={4} maxLength={2000} value={caption} onChange={e => setCaption(e.target.value)}/></label><ErrorNotice error={error}/><div className="form-actions"><button className="button primary" disabled={busy}>{busy ? '保存中…' : '保存图注'}</button></div></form></Modal>}</>;
}
