import Link from 'next/link';
import {RollForm} from '@/components/roll/RollForm';
export default function NewRollPage() {return <div className="narrow-page"><Link className="back-link" href="/">← 胶卷档案</Link><section className="page-heading"><p className="eyebrow">A NEW CHAPTER</p><h1>开始新的一卷<span className="heading-period">.</span></h1><p className="intro">先记录拍摄信息，冲洗和照片可以稍后添加。</p></section><RollForm/></div>;}
