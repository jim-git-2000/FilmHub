'use client';
import Link from 'next/link';
import {Stats, Usage} from '@/types';
import {useResource} from '@/lib/api';
import {Empty, ErrorNotice, Loading} from '@/components/layout/Feedback';
function UsageChart({title, data}: {title: string; data: Usage[]}) {
  const maximum = Math.max(1, ...data.map(item => item.count));
  return <section className="usage-chart"><h2>{title}</h2>{data.length ? <><p className="muted">最常使用 · {data[0].name}</p><ul>{data.map(item => <li key={item.name}><div><span>{item.name}</span><span className="mono">{item.count} 卷</span></div><div className="bar-track"><div style={{width: `${item.count / maximum * 100}%`}}/></div></li>)}</ul></> : <p className="muted">还没有使用记录</p>}</section>;
}
export default function StatsPage() {
  const resource = useResource<Stats>('/stats'), stats = resource.data;
  return <><section className="page-heading"><p className="eyebrow">A YEAR IN LIGHT</p><h1>光影的足迹<span className="heading-period">.</span></h1><p className="intro">回望拍过的每一卷，也期待下一次按下快门。</p></section><ErrorNotice error={resource.error} retry={resource.reload}/>{resource.loading ? <Loading/> : stats && <><div className="stat-totals">{[['胶卷总数', stats.total_rolls, 'ROLLS'], ['总照片数', stats.total_photos, 'FRAMES'], ['今年拍摄', stats.this_year, String(stats.year)]].map(([label, value, suffix]) => <div key={label}><span>{label}</span><strong>{value}<small>{suffix}</small></strong></div>)}</div>{stats.total_rolls ? <><section className="monthly-section"><div className="section-heading"><h2>每月拍摄<span className="english-label">{stats.year} / ROLLS BY MONTH</span></h2><span className="muted">按开始日期</span></div><div className="monthly-chart" role="img" aria-label={`${stats.year} 年每月胶卷数：${stats.months.map(item => `${item.name} 月 ${item.count} 卷`).join('，')}`}>{stats.months.map(item => <div className="month" key={item.name}><span className="mono">{item.count}</span><div className="month-column"><div style={{height: `${item.count / Math.max(1, ...stats.months.map(m => m.count)) * 100}%`}}/></div><span className="mono">{item.name}</span></div>)}</div></section><div className="usage-grid"><UsageChart title="常用胶片" data={stats.films}/><UsageChart title="常用相机" data={stats.cameras}/><UsageChart title="常用镜头" data={stats.lenses}/></div></> : <Empty title="故事刚刚开始"><p>记录第一卷后，这里会逐渐显现你的拍摄习惯。</p><Link className="button" href="/rolls/new">新增胶卷</Link></Empty>}</>}</>;
}
