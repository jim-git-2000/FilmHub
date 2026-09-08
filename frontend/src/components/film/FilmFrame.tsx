import {Photo} from '@/types';
import {frameNumber} from '@/lib/api';
export function FilmFrame({photo, variant = 'card', label = 'FILMHUB', priority = false}: {photo?: Photo | null; variant?: 'card' | 'hero' | 'thumbnail' | 'photo'; label?: string; priority?: boolean}) {
  return <div className={`film-frame film-${variant}`}>
    <div className="film-edge" aria-hidden="true"/>
    <div className="film-image">{photo ? <img src={variant === 'card' || variant === 'thumbnail' ? photo.thumbnail_url : photo.url} width={photo.width} height={photo.height} alt={photo.caption || `第 ${frameNumber(photo.frame_number)} 张照片`} loading={priority ? 'eager' : 'lazy'} decoding="async"/> : <div className="unexposed"><span>FILMHUB</span><strong>待显影的记忆</strong><small>YOUR NEXT STORY, ON FILM.</small></div>}</div>
    <div className="film-inscription" aria-hidden="true"><span>{label}</span><span>{photo ? `${frameNumber(photo.frame_number)} ▸` : '○ UNEXPOSED'}</span></div>
    <div className="film-edge" aria-hidden="true"/>
  </div>;
}
