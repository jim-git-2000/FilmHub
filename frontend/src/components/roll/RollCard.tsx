import Link from 'next/link';
import {Roll, statusLabels} from '@/types';
import {rollNumber, formatDate} from '@/lib/api';
import {FilmFrame} from '@/components/film/FilmFrame';
export function RollCard({roll}: {roll: Roll}) {
  return <Link href={`/rolls/${roll.id}`} className="roll-card">
    <FilmFrame photo={roll.cover} label={roll.film_stock}/>
    <div className="card-kicker"><span className="mono">ROLL {rollNumber(roll.roll_number)}</span><span className={`status status-${roll.status}`}>{statusLabels[roll.status]}</span></div>
    <h2>{roll.title || roll.film_stock}</h2>
    <p className="card-film">{roll.film_stock}{roll.is_favorite && <span aria-label="含收藏照片"> · ★</span>}</p>
    <div className="card-meta"><span>{roll.location || '地点未记录'}<span className="meta-dot">·</span>{roll.camera}</span><span className="mono">{formatDate(roll.started_at || roll.created_at).slice(0, 7)}</span></div>
  </Link>;
}
