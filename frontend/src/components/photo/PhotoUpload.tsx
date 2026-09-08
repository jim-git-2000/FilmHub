'use client';
import {useRef, useState} from 'react';
import {api, message} from '@/lib/api';
import {ErrorNotice} from '@/components/layout/Feedback';
export function PhotoUpload({rollId, done}: {rollId: number; done: () => Promise<void>}) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false), [hover, setHover] = useState(false), [error, setError] = useState(''), [progress, setProgress] = useState({current: 0, total: 0}), [failed, setFailed] = useState<File[]>([]), [notice, setNotice] = useState('');
  async function upload(files: File[]) {
    if (busy || !files.length) return;
    setError(''); setNotice('');
    if (files.length > 40) {setError('每次最多选择 40 张照片，请分批上传。'); return;}
    if (files.some(f => !['image/jpeg', 'image/png', 'image/webp'].includes(f.type) || f.size > 50 * 1024 * 1024)) {setError('请选择 JPEG、PNG 或 WebP，每张不超过 50 MB。'); return;}
    setBusy(true); setFailed([]); setProgress({current: 0, total: files.length});
    const failures: File[] = [];
    // 按文件名自然排序逐张提交，显示实际完成数，并只重试失败项。
    const sorted = [...files].sort((a, b) => a.name.localeCompare(b.name, undefined, {numeric: true}));
    for (const [index, file] of sorted.entries()) {
      const data = new FormData(); data.append('files', file);
      try {await api(`/rolls/${rollId}/photos`, {method: 'POST', body: data});} catch (err) {failures.push(file); setError(`${file.name}：${message(err)}`);}
      setProgress({current: index + 1, total: files.length});
    }
    setFailed(failures); setBusy(false);
    setNotice(`已上传 ${files.length - failures.length} / ${files.length} 张照片${failures.length ? `，${failures.length} 张未完成。` : '。'}`);
    if (input.current) input.current.value = '';
    await done();
  }
  return <div className="upload-section"><div className={`drop-zone ${hover ? 'drag-over' : ''}`} onDragOver={e => {e.preventDefault(); if (!busy) setHover(true);}} onDragLeave={() => setHover(false)} onDrop={e => {e.preventDefault(); setHover(false); void upload(Array.from(e.dataTransfer.files));}}><span className="upload-symbol" aria-hidden="true">＋</span><h3>{busy ? `正在上传 ${progress.current} / ${progress.total}` : '把这一卷的照片放在这里'}</h3><p>拖入照片，或选择文件 · 每批最多 40 张，每张 50 MB</p><p className="muted">JPEG / PNG / WebP · 初始顺序按文件名排列</p><input ref={input} type="file" accept="image/jpeg,image/png,image/webp" multiple className="sr-only" id="photo-files" disabled={busy} onChange={e => void upload(Array.from(e.target.files || []))}/><button type="button" className="button" disabled={busy} onClick={() => input.current?.click()}>{busy ? '上传中…' : '选择照片'}</button>{busy && <progress max={progress.total} value={progress.current} aria-label="照片上传进度"/>}</div><ErrorNotice error={error}/>{notice && <p className="notice" role="status">{notice}</p>}{!!failed.length && <button className="button" disabled={busy} onClick={() => void upload(failed)}>重试 {failed.length} 张未完成照片</button>}</div>;
}
