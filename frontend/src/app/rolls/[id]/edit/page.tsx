'use client';
import Link from 'next/link';
import {useParams} from 'next/navigation';
import {useResource} from '@/lib/api';
import {Roll} from '@/types';
import {RollForm} from '@/components/roll/RollForm';
import {ErrorNotice, Loading} from '@/components/layout/Feedback';
export default function EditRollPage() {const {id} = useParams<{id: string}>(); const roll = useResource<Roll>(`/rolls/${id}`); return <div className="narrow-page"><Link className="back-link" href={`/rolls/${id}`}>← 返回这一卷</Link><section className="page-heading"><p className="eyebrow">FIELD NOTES</p><h1>编辑胶卷<span className="heading-period">.</span></h1></section><ErrorNotice error={roll.error} retry={roll.reload}/>{roll.loading ? <Loading/> : roll.data && <RollForm roll={roll.data}/>}</div>;}
