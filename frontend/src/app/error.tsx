'use client';
export default function ErrorPage({reset}: {error: Error; reset: () => void}) {return <div className="empty"><h1>页面暂时未能打开</h1><p>已保存的档案仍在，请重新尝试。</p><button className="button" onClick={reset}>重新打开</button></div>;}
