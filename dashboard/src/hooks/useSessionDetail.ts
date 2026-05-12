'use client'
import { useEffect, useState } from 'react'
import { fetchEvents, fetchSession, sseUrl } from '@/lib/api'
import type { Session, StreamEvent, StreamHealth } from '@/types'
import { useSSE } from './useSSE'

interface SSEDetailEvent {
  type: string
  status?: string
  stream: string
  seq: number | null
  received_at: string
  data: Record<string, unknown>
  health: StreamHealth[]
}

export function useSessionDetail(id: string) {
  const [session, setSession] = useState<Session | null>(null)
  const [events, setEvents] = useState<StreamEvent[]>([])

  useEffect(() => {
    fetchSession(id).then(setSession).catch(console.error)

    Promise.all([
      fetchEvents(id),
      fetchEvents(id, 'review'),
      fetchEvents(id, 'transcode'),
    ]).then(([general, reviewEvts, transcodeEvts]) => {
      const seen = new Set<string>()
      const merged = [...general, ...reviewEvts, ...transcodeEvts].filter(e => {
        const key = String(e.id)
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      setEvents(merged)
    }).catch(console.error)
  }, [id])

  useSSE(sseUrl(`/sessions/${id}/stream`), (data: unknown) => {
    const msg = data as SSEDetailEvent

    if (msg.type === 'status_updated') {
      setSession(prev => prev ? { ...prev, status: msg.status as Session['status'] } : prev)
      return
    }

    if (msg.type !== 'event') return

    setSession(prev => (prev ? { ...prev, stream_health: msg.health } : prev))

    setEvents(prev => {
      const next: StreamEvent = {
        id: `${msg.stream}-${msg.seq ?? Date.now()}`,
        session_id: id,
        stream: msg.stream,
        seq: msg.seq,
        payload: msg.data,
        received_at: msg.received_at,
      }
      return [next, ...prev].slice(0, 100)
    })
  })

  return { session, events }
}
