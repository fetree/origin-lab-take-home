import type { Session, SessionListItem, Stats, StreamEvent } from '@/types'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json() as Promise<T>
}

export const fetchSessions = () => get<SessionListItem[]>('/sessions')
export const fetchSession = (id: string) => get<Session>(`/sessions/${id}`)
export const fetchEvents = (id: string, stream?: string) =>
  get<StreamEvent[]>(`/sessions/${id}/events${stream ? `?stream=${stream}` : ''}`)
export const fetchStats = () => get<Stats>('/sessions/stats')
export const sseUrl = (path: string) => `${API}${path}`
