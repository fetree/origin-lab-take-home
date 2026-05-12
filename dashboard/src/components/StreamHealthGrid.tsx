'use client'
import type { StreamHealth } from '@/types'

const STREAM_DOT: Record<string, string> = {
  lifecycle:    'bg-gray-400',
  telemetry:    'bg-blue-500',
  upload:       'bg-cyan-500',
  input:        'bg-green-500',
  camera:       'bg-violet-500',
  audio_levels: 'bg-pink-500',
  transcode:    'bg-orange-500',
  quality:      'bg-yellow-500',
  review:       'bg-red-500',
}

const TERMINAL = new Set(['approved', 'rejected', 'failed'])

function status(h: StreamHealth, sessionStatus: string): { label: string; border: string; labelColor: string } {
  if (h.error_count > 0)
    return { label: 'Error', border: 'border-red-300', labelColor: 'text-red-600' }
  if (TERMINAL.has(sessionStatus))
    return { label: 'Completed', border: 'border-gray-200', labelColor: 'text-gray-400' }
  if (h.last_seen_at && h.event_count > 0) {
    const age = Date.now() - new Date(h.last_seen_at).getTime()
    if (age > 30_000)
      return { label: 'Stalled', border: 'border-amber-300', labelColor: 'text-amber-600' }
  }
  return { label: 'Healthy', border: 'border-green-200', labelColor: 'text-green-600' }
}

function timeAgo(iso: string | null): string {
  if (!iso) return 'never'
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (secs < 2) return '<1s ago'
  if (secs < 60) return `${secs}s ago`
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`
  return `${Math.floor(secs / 3600)}h ago`
}

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return String(n)
}

interface Props { health: StreamHealth[]; sessionStatus: string }

export default function StreamHealthGrid({ health, sessionStatus }: Props) {
  if (health.length === 0)
    return <p className="text-gray-400 text-sm">No stream data yet.</p>

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
      {health.map(h => {
        const s = status(h, sessionStatus)
        return (
          <div key={h.stream} className={`bg-white border rounded-lg p-3 ${s.border}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${STREAM_DOT[h.stream] ?? 'bg-gray-400'}`} />
              <span className="font-medium text-sm truncate">{h.stream}</span>
              <span className={`ml-auto text-xs ${s.labelColor}`}>{s.label}</span>
            </div>
            <div className="text-xs text-gray-500 space-y-0.5">
              <div>{fmt(h.event_count)} events</div>
              <div>Last: {timeAgo(h.last_seen_at)}</div>
              {h.error_count > 0 && (
                <div className="text-red-500">{h.error_count} errors</div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
