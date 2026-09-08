'use client';
export function ErrorNotice({error, retry}: {error: string; retry?: () => void}) {
  return error ? <div className="notice error" role="alert">{error}{retry && <button type="button" className="text-button" onClick={retry}>重试</button>}</div> : null;
}
export function Loading() {return <div className="loading" role="status"><span className="loading-dot"/>正在打开档案…</div>;}
export function Empty({title, children}: {title: string; children?: React.ReactNode}) {return <div className="empty"><span className="eyebrow">ROOM FOR MEMORIES</span><h2>{title}</h2>{children}</div>;}
