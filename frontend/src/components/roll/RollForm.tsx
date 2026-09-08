'use client';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import {FormEvent, useEffect, useState} from 'react';
import {Library, LibraryItem, LibraryKind, Roll, Status, statusLabels} from '@/types';
import {api, json, message, useResource} from '@/lib/api';
import {AddLibraryItem} from '@/components/library/AddLibraryItem';
import {ErrorNotice, Loading} from '@/components/layout/Feedback';

type Form = {film_stock_id: string; camera_id: string; lens_ids: number[]; shot_iso: string; started_at: string; finished_at: string; location: string; title: string; description: string; expected_frames: string; status: Status; roll_number: string};
const blank: Form = {film_stock_id: '', camera_id: '', lens_ids: [], shot_iso: '', started_at: '', finished_at: '', location: '', title: '', description: '', expected_frames: '36', status: 'shooting', roll_number: ''};
function fromRoll(roll: Roll): Form {return {...blank, film_stock_id: String(roll.film_stock_id), camera_id: String(roll.camera_id), lens_ids: roll.lenses.map(l => l.id), shot_iso: roll.shot_iso?.toString() || '', started_at: roll.started_at || '', finished_at: roll.finished_at || '', location: roll.location, title: roll.title, description: roll.description, expected_frames: String(roll.expected_frames), status: roll.status, roll_number: String(roll.roll_number)};}
export function RollForm({roll}: {roll?: Roll}) {
  const library = useResource<Library>('/library'), router = useRouter();
  const [form, setForm] = useState<Form>(roll ? fromRoll(roll) : blank);
  const [dialog, setDialog] = useState<LibraryKind | null>(null), [error, setError] = useState(''), [notice, setNotice] = useState(''), [busy, setBusy] = useState(false);
  useEffect(() => {
    if (roll) return;
    try {
      const saved = localStorage.getItem('filmhub-roll-draft');
      if (saved) {const value = JSON.parse(saved); if (value && typeof value === 'object' && Array.isArray(value.lens_ids)) {setForm({...blank, ...value}); setNotice('已恢复这台设备上的草稿。');}}
    } catch {setNotice('浏览器未能读取草稿，可以直接创建胶卷。');}
  }, [roll]);
  function field<K extends keyof Form>(key: K, value: Form[K]) {setForm(current => ({...current, [key]: value}));}
  function draft() {
    try {localStorage.setItem('filmhub-roll-draft', JSON.stringify(form)); setNotice('草稿已保存在当前浏览器，下次打开会自动恢复。');} catch {setError('浏览器无法保存草稿，请直接创建胶卷。');}
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setBusy(true);
    const payload = {...form, film_stock_id: Number(form.film_stock_id), camera_id: Number(form.camera_id), shot_iso: form.shot_iso ? Number(form.shot_iso) : null, expected_frames: Number(form.expected_frames), ...(form.roll_number ? {roll_number: Number(form.roll_number)} : {})} as Record<string, unknown>;
    if (!form.roll_number) delete payload.roll_number;
    try {
      const result = await api<Roll>(roll ? `/rolls/${roll.id}` : '/rolls', json(roll ? 'PUT' : 'POST', payload));
      if (!roll) {try {localStorage.removeItem('filmhub-roll-draft');} catch { /* 已保存的胶卷不受浏览器存储限制影响。 */ }}
      router.push(`/rolls/${result.id}`); router.refresh();
    } catch (err) {setError(message(err));} finally {setBusy(false);}
  }
  async function added(kind: LibraryKind, item: LibraryItem) {
    library.setData(current => current ? {...current, [kind]: [...current[kind], item]} : current);
    if (kind === 'films') field('film_stock_id', String(item.id));
    else if (kind === 'cameras') field('camera_id', String(item.id));
    else setForm(current => ({...current, lens_ids: [...current.lens_ids, item.id]}));
    setDialog(null);
  }
  if (library.loading && !library.data) return <Loading/>;
  return <><ErrorNotice error={library.error} retry={library.reload}/><form onSubmit={submit} className="roll-form"><fieldset disabled={busy}>
    <section className="form-section"><div className="section-heading"><h2><span className="section-number">01</span>这一卷，用什么拍？</h2><span className="muted">* 为必填</span></div><div className="form-grid">
      <label>胶片 *<select required value={form.film_stock_id} onChange={e => e.target.value === '__new' ? setDialog('films') : field('film_stock_id', e.target.value)}><option value="">选择胶片</option>{library.data?.films.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}<option value="__new">＋ 新增胶片</option></select></label>
      <label>相机 *<select required value={form.camera_id} onChange={e => e.target.value === '__new' ? setDialog('cameras') : field('camera_id', e.target.value)}><option value="">选择相机</option>{library.data?.cameras.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}<option value="__new">＋ 新增相机</option></select></label>
      <div className="full-width"><span className="field-label">镜头 <span className="muted">可多选</span></span><div className="lens-options">{library.data?.lenses.map(item => <label className="lens-choice" key={item.id}><input type="checkbox" checked={form.lens_ids.includes(item.id)} onChange={e => field('lens_ids', e.target.checked ? [...form.lens_ids, item.id] : form.lens_ids.filter(id => id !== item.id))}/>{item.name}</label>)}<button type="button" className="text-button" onClick={() => setDialog('lenses')}>＋ 新增镜头</button></div></div>
      <label>拍摄 EI<input type="number" min="1" max="102400" placeholder="例如 200" value={form.shot_iso} onChange={e => field('shot_iso', e.target.value)}/></label><label>预计张数<input required type="number" min="1" max="1000" value={form.expected_frames} onChange={e => field('expected_frames', e.target.value)}/></label>
    </div></section>
    <section className="form-section"><h2><span className="section-number">02</span>记下故事的开始</h2><div className="form-grid"><label>开始日期<input type="date" value={form.started_at} onChange={e => field('started_at', e.target.value)}/></label><label>地点<input maxLength={200} placeholder="城市、街道，或某个特别的地方" value={form.location} onChange={e => field('location', e.target.value)}/></label><label className="full-width">标题<input maxLength={200} placeholder="给这一卷起个名字" value={form.title} onChange={e => field('title', e.target.value)}/></label><label className="full-width">备注<textarea rows={4} maxLength={10000} placeholder="关于这次拍摄，想记住的事情…" value={form.description} onChange={e => field('description', e.target.value)}/></label></div>
      <details className="advanced" open={roll ? true : undefined}><summary>{roll ? '拍摄进度与编号' : '更多信息 · 自定义胶卷编号'}</summary><div className="form-grid"><label>胶卷编号<input type="number" min="1" max="2147483647" disabled={!!roll} placeholder="自动编号" value={form.roll_number} onChange={e => field('roll_number', e.target.value)}/></label>{roll && <><label>结束日期<input type="date" min={form.started_at || undefined} value={form.finished_at} onChange={e => field('finished_at', e.target.value)}/></label><label>状态<select value={form.status} onChange={e => field('status', e.target.value as Status)}>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><small className="muted">已有冲洗、扫描或照片时，状态至少保持在相应阶段。</small></label></>}</div></details>
    </section><ErrorNotice error={error}/>{notice && <p className="notice" role="status">{notice}</p>}<div className="form-actions"><Link href={roll ? `/rolls/${roll.id}` : '/'} className="button">取消</Link>{!roll && <button type="button" className="button" onClick={draft}>保存草稿</button>}<button className="button primary" disabled={busy || !library.data}>{busy ? '保存中…' : roll ? '保存修改' : '创建胶卷 →'}</button></div>
  </fieldset></form>{dialog && <AddLibraryItem kind={dialog} close={() => setDialog(null)} saved={item => void added(dialog, item)}/>}</>;
}
