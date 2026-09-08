'use client';
import {FormEvent, useState} from 'react';
import {ProcessRecord} from '@/types';
import {api, json, message} from '@/lib/api';
import {ErrorNotice} from '@/components/layout/Feedback';
import {Modal} from '@/components/layout/Modal';
type Field = {key: string; label: string; type?: string; placeholder?: string; min?: number; max?: number; step?: string};
const common: Record<string, Field[]> = {
  development: [{key: 'lab_name', label: '冲洗店'}, {key: 'process', label: '冲洗工艺', placeholder: 'C-41 / E-6 / 黑白'}, {key: 'developed_at', label: '冲洗日期', type: 'date'}, {key: 'push_pull', label: 'Push / Pull（档）', type: 'number', min: -10, max: 10, step: '0.5'}],
  scan: [{key: 'scanner_model', label: '扫描设备', placeholder: 'Noritsu HS-1800'}, {key: 'lab_name', label: '扫描店'}, {key: 'resolution_width', label: '分辨率 · 宽', type: 'number', min: 1, max: 100000}, {key: 'resolution_height', label: '分辨率 · 高', type: 'number', min: 1, max: 100000}, {key: 'scanned_at', label: '扫描日期', type: 'date'}, {key: 'file_format', label: '文件格式', placeholder: 'JPEG'}],
};
const more: Field[] = [{key: 'developer', label: '药水'}, {key: 'temperature_c', label: '温度（°C）', type: 'number', min: 0, max: 100, step: '0.1'}, {key: 'development_time_sec', label: '冲洗时间（秒）', type: 'number', min: 0, max: 86400}];
const cost: Field[] = [{key: 'cost', label: '费用', type: 'number', min: 0, max: 1000000, step: '0.01'}, {key: 'currency', label: '币种', placeholder: 'CNY'}];
export function ProcessForm({rollId, kind, record, close, saved}: {rollId: number; kind: 'development' | 'scan'; record: ProcessRecord | null; close: () => void; saved: () => void}) {
  const [values, setValues] = useState<Record<string, string>>(() => {const result: Record<string, string> = {method: 'lab', push_pull: '0', currency: 'CNY', file_format: 'JPEG'}; if (record) for (const [key, value] of Object.entries(record)) result[key] = value === null ? '' : String(value); return result;});
  const [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const label = kind === 'development' ? '冲洗' : '扫描';
  function input(field: Field) {return <label key={field.key}>{field.label}<input type={field.type || 'text'} maxLength={200} min={field.min} max={field.max} step={field.step} placeholder={field.placeholder} value={values[field.key] || ''} onChange={e => setValues({...values, [field.key]: e.target.value})}/></label>;}
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    const fields = [...common[kind], ...(kind === 'development' ? more : []), ...cost];
    const payload: Record<string, string | number | null> = {method: values.method, notes: values.notes || ''};
    for (const field of fields) payload[field.key] = field.type === 'number' ? (values[field.key] ? Number(values[field.key]) : field.key === 'push_pull' ? 0 : null) : values[field.key] || (field.type === 'date' ? null : '');
    try {await api(`/rolls/${rollId}/${kind}`, json('PUT', payload)); saved();} catch (err) {setError(message(err));} finally {setBusy(false);}
  }
  async function remove() {
    if (!confirm(`删除这条${label}记录？胶卷状态会保留。`)) return;
    setBusy(true); setError(''); try {await api(`/rolls/${rollId}/${kind}`, json('DELETE')); saved();} catch (err) {setError(message(err));} finally {setBusy(false);}
  }
  return <Modal title={`${record ? '编辑' : '添加'}${label}记录`} close={() => {if (!busy) close();}}><form onSubmit={submit}><fieldset disabled={busy}><label>{label}方式<select value={values.method} onChange={e => setValues({...values, method: e.target.value})}><option value="lab">送店</option><option value="self">自助</option></select></label><div className="form-grid">{common[kind].map(input)}</div><label>备注<textarea rows={3} maxLength={10000} value={values.notes || ''} onChange={e => setValues({...values, notes: e.target.value})}/></label><details className="advanced"><summary>更多信息</summary><div className="form-grid">{[...(kind === 'development' ? more : []), ...cost].map(input)}</div></details><ErrorNotice error={error}/><div className="form-actions">{record && <button type="button" className="text-button danger-text" onClick={remove}>删除记录</button>}<button type="button" className="button" onClick={close}>取消</button><button className="button primary">{busy ? '保存中…' : '保存记录'}</button></div></fieldset></form></Modal>;
}
