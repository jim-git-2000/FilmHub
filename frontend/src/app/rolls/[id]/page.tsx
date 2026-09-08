'use client';
import Link from 'next/link';
import {useParams, useRouter} from 'next/navigation';
import {useState} from 'react';
import {Roll, statusLabels} from '@/types';
import {api, formatDate, json, message, rollNumber, useResource} from '@/lib/api';
import {FilmFrame} from '@/components/film/FilmFrame';
import {Empty, ErrorNotice, Loading} from '@/components/layout/Feedback';
import {RollMetadata} from '@/components/roll/RollMetadata';
import {RollContactSheet} from '@/components/roll/RollContactSheet';
import {RollPhotoFeed} from '@/components/roll/RollPhotoFeed';
import {ProcessForm} from '@/components/roll/ProcessForm';
import {PhotoUpload} from '@/components/photo/PhotoUpload';
import {PhotoSorter} from '@/components/photo/PhotoSorter';
export default function RollDetailPage() {
  const {id} = useParams<{id: string}>(), router = useRouter();
  const resource = useResource<Roll>(`/rolls/${id}`);
  const [manage, setManage] = useState(false), [record, setRecord] = useState<'development' | 'scan' | null>(null), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  async function lifecycle(archive = false) {
    setBusy(true); setError('');
    const now = new Date(); const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    try {await api(`/rolls/${id}`, json('PUT', archive ? {status: 'archived'} : {finished_at: today})); await resource.reload();} catch (err) {setError(message(err));} finally {setBusy(false);}
  }
  async function remove() {
    if (!confirm('删除整卷胶片及所有照片、冲洗和扫描记录？此操作无法撤销。')) return;
    setBusy(true); setError(''); try {await api(`/rolls/${id}`, json('DELETE')); router.push('/');} catch (err) {setError(message(err)); setBusy(false);}
  }
  const roll = resource.data;
  return <><div className="detail-top"><Link className="back-link" href="/">← 胶卷档案</Link>{roll && <Link className="button small" href={`/rolls/${id}/edit`}>编辑胶卷 ↗</Link>}</div><ErrorNotice error={resource.error} retry={resource.reload}/>{!roll ? resource.loading && <Loading/> : <>
    <FilmFrame photo={roll.cover} variant="hero" label={roll.film_stock} priority/>
    <section className="roll-title"><div><p className="eyebrow">ROLL {rollNumber(roll.roll_number)} <span> / </span> {formatDate(roll.started_at || roll.created_at).slice(0, 7)}</p><h1>{roll.title || roll.film_stock}</h1>{roll.description && <p className="roll-description">{roll.description}</p>}</div><div className="roll-progress"><span className={`status status-${roll.status}`}>{statusLabels[roll.status]}</span>{roll.status === 'shooting' && <button className="text-button" disabled={busy} onClick={() => void lifecycle()}>结束拍摄 →</button>}{roll.status === 'scanned' && <button className="text-button" disabled={busy} onClick={() => void lifecycle(true)}>完成归档 →</button>}</div></section>
    <ErrorNotice error={error}/><section className="detail-section metadata-section"><h2>拍摄手记<span className="english-label">ROLL NOTES</span></h2><RollMetadata roll={roll}/><div className="process-grid">{(['development', 'scan'] as const).map(kind => {const data = roll[kind]; return <section key={kind}><div className="section-heading"><h3>{kind === 'development' ? '冲洗' : '扫描'}</h3><button className="text-button" onClick={() => setRecord(kind)}>{data ? '编辑' : '＋ 添加记录'}</button></div>{data ? <><p>{[data.process || data.scanner_model, data.lab_name || (data.method === 'self' ? '自助' : '送店')].filter(Boolean).join(' / ')}</p>{kind === 'scan' && data.resolution_width && data.resolution_height ? <p className="mono muted">{data.resolution_width} × {data.resolution_height} · {data.file_format}</p> : null}{kind === 'development' && Number(data.push_pull) !== 0 && <p className="muted">Push / Pull {Number(data.push_pull) > 0 ? '+' : ''}{data.push_pull} 档</p>}<p className="mono muted">{formatDate(String(data.developed_at || data.scanned_at || ''))}</p>{data.notes && <p className="record-notes">{data.notes}</p>}</> : <p className="muted">{kind === 'development' ? '等光影慢慢显现。冲洗后，在这里留一笔。' : '记录扫描设备和日期，让影像有迹可循。'}</p>}</section>;})}</div></section>
    <div className="photo-management-toggle"><span className="eyebrow">THE PHOTOGRAPHS / {roll.photos.length}</span><button className="button" onClick={() => setManage(!manage)} aria-expanded={manage}>{manage ? '收起照片管理' : '＋ 上传 / 管理照片'}</button></div>{manage && <section className="photo-management"><PhotoUpload rollId={roll.id} done={resource.reload}/>{!!roll.photos.length && <PhotoSorter rollId={roll.id} photos={roll.photos} changed={resource.reload}/>}</section>}
    {roll.photos.length ? <><RollContactSheet photos={roll.photos} label={roll.film_stock}/><RollPhotoFeed roll={roll}/></> : <Empty title="照片，等冲扫后再见"><p>这一卷的拍摄信息已经保存。上传后，会在这里生成整卷总览与单张展示。</p>{!manage && <button className="button" onClick={() => setManage(true)}>上传照片</button>}</Empty>}
    <div className="detail-bottom"><Link href="/" className="back-link">← 回到胶卷档案</Link><button className="text-button danger-text" disabled={busy} onClick={() => void remove()}>删除这一卷</button></div>
    {record && <ProcessForm rollId={roll.id} kind={record} record={roll[record]} close={() => setRecord(null)} saved={() => {setRecord(null); void resource.reload();}}/>}
  </>}</>;
}
