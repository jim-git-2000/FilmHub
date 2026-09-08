'use client';
import {useState} from 'react';
import {Library, LibraryItem, LibraryKind} from '@/types';
import {api, json, message, useResource} from '@/lib/api';
import {AddLibraryItem, libraryLabels} from '@/components/library/AddLibraryItem';
import {ErrorNotice, Loading} from '@/components/layout/Feedback';
export default function LibraryPage() {
  const resource = useResource<Library>('/library');
  const [dialog, setDialog] = useState<{kind: LibraryKind; item?: LibraryItem} | null>(null);
  const [error, setError] = useState(''), [busy, setBusy] = useState(false);
  async function remove(kind: LibraryKind, item: LibraryItem) {
    if (!window.confirm(`删除“${item.name}”？正在使用的条目会保留。`)) return;
    setBusy(true); setError('');
    try {await api(`/library/${kind}/${item.id}`, json('DELETE')); await resource.reload();} catch (err) {setError(message(err));} finally {setBusy(false);}
  }
  return <><section className="page-heading"><p className="eyebrow">THE ESSENTIALS</p><h1>器材库<span className="heading-period">.</span></h1><p className="intro">熟悉的胶片、相机和镜头，下一卷直接选用。</p></section><ErrorNotice error={error || resource.error} retry={resource.reload}/>{resource.loading ? <Loading/> : resource.data && <div className="library-grid">{(Object.keys(libraryLabels) as LibraryKind[]).map((kind, index) => <section className="library-section" key={kind}><div className="section-heading"><h2><span className="section-number">0{index + 1}</span>{libraryLabels[kind]}</h2><button className="text-button" onClick={() => setDialog({kind})}>＋ 添加{libraryLabels[kind]}</button></div><p className="eyebrow library-subtitle">{['FILM STOCKS', 'CAMERAS', 'LENSES'][index]} / {resource.data![kind].length}</p><ul className="library-list">{resource.data![kind].map(item => <li key={item.id}><span>{item.name}</span><details className="item-menu"><summary aria-label={`${item.name} 操作`}>···</summary><div><button onClick={() => setDialog({kind, item})}>重命名</button><button className="danger-text" disabled={busy} onClick={() => remove(kind, item)}>删除</button></div></details></li>)}</ul>{!resource.data![kind].length && <p className="muted library-empty">还没有{libraryLabels[kind]}条目。<br/>添加常用名称，或在创建胶卷时随手加入。</p>}</section>)}</div>}{dialog && <AddLibraryItem {...dialog} close={() => setDialog(null)} saved={() => {setDialog(null); void resource.reload();}}/>}</>;
}
