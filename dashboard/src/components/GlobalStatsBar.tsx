'use client'
import { useEffect, useState } from 'react'
import { fetchStats, sseUrl } from '@/lib/api'
import { useSSE } from '@/hooks/useSSE'
import StatsBar from './StatsBar'
import type { Stats } from '@/types'

export default function GlobalStatsBar() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [eventsHistory, setEventsHistory] = useState<number[]>([])

  const refresh = () =>
    fetchStats()
      .then(s => {
        setStats(s)
        setEventsHistory(prev => [...prev.slice(-59), s.events_per_second])
      })
      .catch(console.error)

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 2000)
    return () => clearInterval(interval)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useSSE(sseUrl('/sessions/stream'), refresh)

  return <StatsBar stats={stats} eventsHistory={eventsHistory} />
}
