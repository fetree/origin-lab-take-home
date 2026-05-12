'use client'
import type { Stats } from '@/types'

const STATUS_COLORS: Record<string, string> = {
  created:    'bg-gray-100 text-gray-600',
  uploading:  'bg-blue-100 text-blue-700',
  processing: 'bg-amber-100 text-amber-700',
  review:     'bg-purple-100 text-purple-700',
  approved:   'bg-green-100 text-green-700',
  rejected:   'bg-red-100 text-red-700',
  failed:     'bg-red-100 text-red-700',
  paused:     'bg-orange-100 text-orange-700',
}

function Sparkline({ data }: { data: number[] }) {
  if (data.length < 2) {
    return <svg width={120} height={32} className="opacity-20"><rect width={120} height={32} rx={4} fill="#3b82f6" /></svg>
  }

  const W = 120, H = 32
  const max = Math.max(...data, 1)
  const pts = data.map((v, i) => [
    (i / (data.length - 1)) * W,
    H - (v / max) * (H - 4) - 2,
  ])
  const line = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  const area = `${line} L${W},${H} L0,${H} Z`
  const [lastX, lastY] = pts[pts.length - 1]

  return (
    <svg width={W} height={H} className="overflow-visible">
      <defs>
        <linearGradient id="evGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#evGrad)" />
      <path d={line} fill="none" stroke="#3b82f6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lastX} cy={lastY} r={3} fill="#3b82f6" />
    </svg>
  )
}

interface Props { stats: Stats | null; eventsHistory: number[] }

export default function StatsBar({ stats, eventsHistory }: Props) {
  if (!stats) return <div className="h-16 bg-white border-b animate-pulse" />

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6 flex-wrap">
      {/* Total */}
      <div className="flex flex-col">
        <span className="text-xs text-gray-400 uppercase tracking-wide">Total</span>
        <span className="text-2xl font-bold text-gray-900">{stats.total_sessions}</span>
      </div>

      <div className="w-px h-10 bg-gray-100" />

      {/* By status */}
      <div className="flex gap-2 flex-wrap items-center">
        {Object.entries(stats.by_status).map(([status, count]) => (
          <span
            key={status}
            className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[status] ?? 'bg-gray-100 text-gray-600'}`}
          >
            {status} {count}
          </span>
        ))}
      </div>

      <div className="w-px h-10 bg-gray-100" />

      {/* Live events sparkline */}
      <div className="flex items-center gap-3">
        <div className="flex flex-col">
          <span className="text-xs text-gray-400 uppercase tracking-wide">Events/sec</span>
          <span className="text-xl font-bold text-blue-600">{stats.events_per_second.toFixed(1)}</span>
        </div>
        <Sparkline data={eventsHistory} />
      </div>

      <div className="w-px h-10 bg-gray-100" />

      {/* Error rate */}
      <div className="flex flex-col ml-auto">
        <span className="text-xs text-gray-400 uppercase tracking-wide">Error rate</span>
        <span className={`text-xl font-bold ${stats.error_rate > 0 ? 'text-red-500' : 'text-gray-400'}`}>
          {(stats.error_rate * 100).toFixed(2)}%
        </span>
      </div>
    </div>
  )
}
