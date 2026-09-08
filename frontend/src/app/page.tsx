'use client';
import Link from 'next/link';
import {useEffect, useState} from 'react';
import {Roll, Stats} from '@/types';
import {useResource} from '@/lib/api';
import {RollCard} from '@/components/roll/RollCard';
import {Empty, ErrorNotice, Loading} from '@/components/layout/Feedback';
export default function ArchivePage() {
  const [search, setSearch] = useState(''), [query, setQuery] = useState(''), [status, setStatus] = useState(''), [year, setYear] = useState('');
  useEffect(() => {const timer = setTimeout(() => setQuery(search), 250); return () => clearTimeout(timer);}, [search]);
  const params = new URLSearchParams({q: query, status, ...(year ? {year} : {})});
  const rolls = useResource<Roll[]>(`/rolls?${params}`);
  const stats = useResource<Stats>('/stats');
  return <div className="archive-page">
    <section className="page-heading archive-heading"><div><p className="eyebrow">THE FILM ARCHIVE <span>—</span> 光阴的切片</p><h1>胶卷档案<span className="heading-period">.</span></h1><p className="intro">用胶片，记录生活的温度。</p></div><div className="archive-index" aria-hidden="true"><span>COLLECT MOMENTS.</span><span>ONE ROLL AT A TIME.</span><strong>{String(stats.data?.total_rolls || 0).padStart(3, '0')}<small> ROLLS</small></strong></div></section>
    <div className="archive-toolbar"><label className="search-field"><span aria-hidden="true">⌕</span><input type="search" aria-label="搜索胶卷" placeholder="搜索胶卷、地点或关键词…" value={search} onChange={e => setSearch(e.target.value)}/>{search && <button type="button" className="icon-button" aria-label="清空搜索" onClick={() => setSearch('')}>×</button>}</label><Link href="/rolls/new" className="button primary">＋ 新增胶卷</Link></div>
    <div className="filter-row"><div className="filter-tabs" aria-label="胶卷状态筛选">{[['', '全部'], ['shooting', '拍摄中'], ['finished', '已拍完'], ['processed', '已冲扫'], ['favorite', '收藏']].map(([value, label]) => <button key={value} aria-pressed={status === value} onClick={() => setStatus(value)}>{label}</button>)}</div><label className="year-filter"><span className="sr-only">年份</span><select value={year} onChange={e => setYear(e.target.value)}><option value="">全部年份</option>{stats.data?.years.map(y => <option key={y}>{y}</option>)}</select></label></div>
    <ErrorNotice error={rolls.error} retry={rolls.reload}/>
    {rolls.loading ? <Loading/> : rolls.data?.length ? <><div className="results-caption mono">{String(rolls.data.length).padStart(2, '0')} ROLLS <span>按拍摄时间排列</span></div><div className="roll-grid">{rolls.data.map(roll => <RollCard key={roll.id} roll={roll}/>)}</div></> : !rolls.error && <Empty title={search || status || year ? '还没有找到这一卷' : '从第一卷开始，留住光阴'}><p>{search || status || year ? '换一个关键词，或清除筛选再看看。' : '记下胶片、相机和出发的日子。照片可以在冲扫后慢慢加入。'}</p>{search || status || year ? <button className="button" onClick={() => {setSearch(''); setStatus(''); setYear('');}}>清除筛选</button> : <Link href="/rolls/new" className="button primary">记录第一卷 →</Link>}</Empty>}
  </div>;
}
