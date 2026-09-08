'use client';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
export function Header() {
  const path = usePathname();
  return <header className="site-header"><div className="header-inner">
    <Link href="/" className="brand" aria-label="FilmHub 首页"><span className="brand-mark" aria-hidden="true">▤</span> FilmHub<span className="brand-note">A PERSONAL FILM ARCHIVE</span></Link>
    <nav aria-label="主导航">{[['/', '胶卷档案'], ['/library', '器材库'], ['/stats', '统计'], ['/settings', '设置']].map(([url, label]) => <Link key={url} href={url} aria-current={(url === '/' ? path === '/' || path.startsWith('/rolls') : path.startsWith(url)) ? 'page' : undefined}>{label}</Link>)}</nav>
  </div></header>;
}
