import type {Metadata} from 'next';
import {Header} from '@/components/layout/Header';
import './globals.css';
export const metadata: Metadata = {title: {default: 'FilmHub · 胶卷档案', template: '%s · FilmHub'}, description: '以每一卷胶片，记录生活的温度。个人胶片拍摄、冲扫记录与摄影档案。'};
export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="zh-CN"><body><a className="skip-link" href="#main">跳转到内容</a><Header/><main id="main">{children}</main><footer className="site-footer"><span>FilmHub <span className="footer-dot">/</span> 每一卷，都值得被记住。</span><span className="mono">MADE OF LIGHT & TIME</span></footer></body></html>;
}
