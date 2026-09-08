'use client';
import {useCallback, useEffect, useRef, useState} from 'react';

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: {'X-FilmHub-Request': '1', ...(options.body && !(options.body instanceof FormData) ? {'Content-Type': 'application/json'} : {}), ...options.headers},
      cache: 'no-store',
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new Error('暂时无法连接档案，请检查服务后重试');
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(typeof data.detail === 'string' ? data.detail : `操作未完成（${response.status}），请重试`);
  }
  return response.status === 204 ? undefined as T : response.json();
}
export const json = (method: string, body?: unknown): RequestInit => ({method, ...(body !== undefined ? {body: JSON.stringify(body)} : {})});
export const message = (error: unknown) => error instanceof Error ? error.message : '操作未完成，请重试';
export const frameNumber = (value: number) => String(value).padStart(2, '0');
export const rollNumber = (value: number) => String(value).padStart(3, '0');
export const formatDate = (value?: string | null) => value ? value.slice(0, 10).replaceAll('-', '.') : '未记录';
export function useResource<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const request = useRef(0);
  const reload = useCallback(async () => {
    const sequence = ++request.current;
    setLoading(true); setError('');
    try {
      const result = await api<T>(path);
      if (sequence === request.current) setData(result);
    } catch (err) {if (sequence === request.current) setError(message(err));}
    finally {if (sequence === request.current) setLoading(false);}
  }, [path]);
  useEffect(() => {setData(null); void reload(); return () => {request.current++;};}, [reload]);
  return {data, error, loading, reload, setData};
}
