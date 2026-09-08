'use client';
import {useEffect, useRef} from 'react';
export function Modal({title, children, close}: {title: string; children: React.ReactNode; close: () => void}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {const dialog = ref.current; dialog?.showModal(); return () => dialog?.close();}, []);
  return <dialog ref={ref} onCancel={event => {event.preventDefault(); close();}} aria-label={title}>
    <div className="dialog-heading"><h2>{title}</h2><button className="icon-button" type="button" onClick={close} aria-label="关闭">×</button></div>{children}
  </dialog>;
}
