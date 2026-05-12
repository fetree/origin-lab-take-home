'use client'
import Link from 'next/link'
import type { SessionListItem, StreamHealth } from '@/types'

const STATUS_STYLES: Record<string, string> = {
  created:    'bg-gray-100 text-gray-600',
  uploading:  'bg-blue-100 text-blue-700',
  processing: 'bg-amber-100 text-amber-700',
  review:     'bg-purple-100 text-purple-700',
  approved:   'bg-green-100 text-green-700',
  rejected:   'bg-red-100 text-red-700',
  failed:     'bg-red-100 text-red-700',
  paused:     'bg-orange-100 text-orange-700',
}

function getHealth(health: StreamHealth[]): { label: string; dot: string } {
  if (health.some(h => h.error_count > 0))
    return { label: 'Error', dot: 'bg-red-500' }
  if (health.some(h => {
    if (!h.last_seen_at || h.event_count === 0) return false
    return Date.now() - new Date(h.last_seen_at).getTime() > 30_000
  }))
    return { label: 'Stalled', dot: 'bg-amber-400' }
  if (health.length === 0)
    return { label: 'No data', dot: 'bg-gray-300' }
  return { label: 'Healthy', dot: 'bg-green-500' }
}

function activeStreams(health: StreamHealth[]): number {
  return health.filter(h => h.event_count > 0).length
}

function timeAgo(iso: string): string {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (secs < 60) return `${secs}s ago`
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`
  return `${Math.floor(secs / 3600)}h ago`
}

interface Props { sessions: SessionListItem[] }

export default function SessionList({ sessions }: Props) {
  if (sessions.length === 0) {
    return (
      <div className="text-center py-20 text-gray-400">
        No sessions yet. Run the simulator to get started.
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
          <tr>
            <th className="px-4 py-3 text-left">Game</th>
            <th className="px-4 py-3 text-left">Operator</th>
            <th className="px-4 py-3 text-left">Resolution</th>
            <th className="px-4 py-3 text-left">Status</th>
            <th className="px-4 py-3 text-left">Streams</th>
            <th className="px-4 py-3 text-left">Health</th>
            <th className="px-4 py-3 text-left">Created</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {sessions.map(s => {
            const health = getHealth(s.stream_health)
            const configured = s.streams?.length ?? 0
            const active = activeStreams(s.stream_health)
            return (
              <tr key={s.id} className="hover:bg-gray-50 cursor-pointer transition-colors">
                <td className="px-4 py-3 font-medium">
                  <Link href={`/sessions/${s.id}`} className="hover:text-blue-600">
                    {s.game_title}
                  </Link>
                </td>
                <td className="px-4 py-3 text-gray-600">{s.operator_name}</td>
                <td className="px-4 py-3 text-gray-600">{s.resolution ?? '—'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[s.status] ?? 'bg-gray-100 text-gray-600'}`}>
                    {s.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {active}/{configured}
                </td>
                <td className="px-4 py-3">
                  <span className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${health.dot}`} />
                    <span className="text-gray-600">{health.label}</span>
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400">{timeAgo(s.created_at)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
