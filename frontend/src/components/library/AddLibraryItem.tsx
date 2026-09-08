'use client';
import {FormEvent, useState} from 'react';
import {LibraryItem, LibraryKind} from '@/types';
import {api, json, message} from '@/lib/api';
import {ErrorNotice} from '@/components/layout/Feedback';
import {Modal} from '@/components/layout/Modal';
export const libraryLabels: Record<LibraryKind, string> = {films: '胶片', cameras: '相机', lenses: '镜头'};
export function AddLibraryItem({kind, item, close, saved}: {kind: LibraryKind; item?: LibraryItem; close: () => void; saved: (item: LibraryItem) => void}) {
  const [name, setName] = useState(item?.name || ''), [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {saved(await api<LibraryItem>(`/library/${kind}${item ? `/${item.id}` : ''}`, json(item ? 'PUT' : 'POST', {name})));}
    catch (err) {setError(message(err));} finally {setBusy(false);}
  }
  return <Modal title={`${item ? '重命名' : '新增'}${libraryLabels[kind]}`} close={() => {if (!busy) close();}}><form onSubmit={submit}><label>名称<input autoFocus required maxLength={200} value={name} onChange={e => setName(e.target.value)} placeholder={{films: 'Kodak Portra 400', cameras: 'Leica M6', lenses: '35mm F2'}[kind]}/></label><ErrorNotice error={error}/><div className="form-actions"><button type="button" className="button" disabled={busy} onClick={close}>取消</button><button className="button primary" disabled={busy || !name.trim()}>{busy ? '保存中…' : item ? '保存' : '添加'}</button></div></form></Modal>;
}
