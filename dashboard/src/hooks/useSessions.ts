'use client'
import { useEffect, useState } from 'react'
import { fetchSessions, fetchStats, sseUrl } from '@/lib/api'
import type { SessionListItem, SessionStatus, Stats } from '@/types'
import { useSSE } from './useSSE'

export function useSessions() {
  const [sessions, setSessions] = useState<SessionListItem[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [eventsHistory, setEventsHistory] = useState<number[]>([])

  const refreshStats = () =>
    fetchStats()
      .then(s => {
        setStats(s)
        setEventsHistory(prev => [...prev.slice(-59), s.events_per_second])
      })
      .catch(console.error)

  useEffect(() => {
    fetchSessions().then(setSessions).catch(console.error)
    refreshStats()

    const interval = setInterval(refreshStats, 2000)
    return () => clearInterval(interval)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useSSE(sseUrl('/sessions/stream'), (data: unknown) => {
    const msg = data as { type: string; session_id: string; status: string }

    if (msg.type === 'session_created') {
      fetchSessions().then(setSessions).catch(console.error)
      refreshStats()
    } else if (msg.type === 'session_updated') {
      setSessions(prev =>
        prev.map(s =>
          s.id === msg.session_id ? { ...s, status: msg.status as SessionStatus } : s
        )
      )
      refreshStats()
    }
  })

  return { sessions, stats, eventsHistory }
}
