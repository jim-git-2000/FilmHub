import {Photo} from '@/types';
import {FilmFrame} from '@/components/film/FilmFrame';
import {frameNumber} from '@/lib/api';
export function RollContactSheet({photos, label}: {photos: Photo[]; label: string}) {return <section className="detail-section" id="contact-sheet"><div className="section-heading"><h2>整卷总览<span className="english-label">CONTACT SHEET</span></h2><span className="muted">{photos.length} 张照片</span></div><div className="contact-sheet">{photos.map(photo => <a key={photo.id} href={`#photo-${photo.frame_number}`} className="contact-photo" aria-label={`查看第 ${photo.frame_number} 张照片`}><FilmFrame photo={photo} variant="thumbnail" label={label}/><span className="mono">{frameNumber(photo.frame_number)}{photo.is_favorite ? ' ★' : ''}</span></a>)}</div></section>;}
