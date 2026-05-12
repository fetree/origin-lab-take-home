'use client'
import { useEffect, useState } from 'react'
import { fetchSessions, sseUrl } from '@/lib/api'
import type { SessionListItem, SessionStatus } from '@/types'
import { useSSE } from './useSSE'

export function useSessions() {
  const [sessions, setSessions] = useState<SessionListItem[]>([])

  useEffect(() => {
    fetchSessions().then(setSessions).catch(console.error)
  }, [])

  useSSE(sseUrl('/sessions/stream'), (data: unknown) => {
    const msg = data as { type: string; session_id: string; status: string }

    if (msg.type === 'session_created') {
      fetchSessions().then(setSessions).catch(console.error)
    } else if (msg.type === 'session_updated') {
      setSessions(prev =>
        prev.map(s =>
          s.id === msg.session_id ? { ...s, status: msg.status as SessionStatus } : s
        )
      )
    }
  })

  return { sessions }
}
