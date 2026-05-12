'use client'
import type { StreamEvent } from '@/types'

const STREAM_BADGE: Record<string, string> = {
  lifecycle:    'bg-gray-100 text-gray-600',
  telemetry:    'bg-blue-100 text-blue-700',
  upload:       'bg-cyan-100 text-cyan-700',
  input:        'bg-green-100 text-green-700',
  camera:       'bg-violet-100 text-violet-700',
  audio_levels: 'bg-pink-100 text-pink-700',
  transcode:    'bg-orange-100 text-orange-700',
  quality:      'bg-yellow-100 text-yellow-700',
  review:       'bg-red-100 text-red-700',
}

function summarize(stream: string, p: Record<string, unknown>): string {
  switch (stream) {
    case 'telemetry':
      return `fps=${p.recording_fps} gpu=${p.gpu_usage_percent}% cpu=${p.cpu_usage_percent}%`
    case 'input':
      if (p.type === 'mouse_move') return `mouse_move (${p.x}, ${p.y})`
      return `${p.type}${p.key ? ` key=${p.key}` : ''}`
    case 'camera':
      return `pos=(${p.px}, ${p.py}, ${p.pz}) yaw=${p.yaw}`
    case 'upload':
      return `${p.file} ${p.percent}%${p.completed ? ' ✓' : ''}`
    case 'audio_levels':
      return `rms=${p.rms_db}dB peak=${p.peak_db}dB${p.clipping ? ' ⚠ CLIP' : ''}`
    case 'transcode':
      return `${p.stage}${p.rendition ? ` ${p.rendition}` : ''}${p.percent != null ? ` ${p.percent}%` : ''}`
    case 'quality':
      return `${p.metric} = ${p.value} / ${p.threshold} ${p.pass ? '✓ PASS' : '✗ FAIL'}`
    case 'review':
      return `${p.decision} by ${p.reviewer}`
    case 'lifecycle':
      return String(p.type ?? '')
    default:
      return JSON.stringify(p).slice(0, 80)
  }
}

function fmtTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

interface Props { events: StreamEvent[] }

export default function EventTimeline({ events }: Props) {
  if (events.length === 0)
    return <p className="text-gray-400 text-sm">Waiting for events…</p>

  return (
    <div className="overflow-y-auto max-h-96 space-y-1 font-mono text-xs">
      {events.map((e, i) => (
        <div key={`${e.id}-${i}`} className="flex items-start gap-2 py-0.5">
          <span className="text-gray-400 flex-shrink-0 w-20">{fmtTime(e.received_at)}</span>
          <span className={`px-1.5 py-0.5 rounded text-xs flex-shrink-0 ${STREAM_BADGE[e.stream] ?? 'bg-gray-100 text-gray-600'}`}>
            {e.stream}
          </span>
          {e.seq != null && (
            <span className="text-gray-300 flex-shrink-0">#{e.seq}</span>
          )}
          <span className="text-gray-700 truncate">{summarize(e.stream, e.payload)}</span>
        </div>
      ))}
    </div>
  )
}
