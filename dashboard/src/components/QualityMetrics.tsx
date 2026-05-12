'use client'
import type { StreamEvent } from '@/types'

interface QualityPayload {
  metric: string
  value: number
  threshold: number
  pass: boolean
  detail?: string
}

interface Props { events: StreamEvent[] }

export default function QualityMetrics({ events }: Props) {
  const metrics = events
    .filter(e => e.stream === 'quality')
    .map(e => e.payload as unknown as QualityPayload)

  if (metrics.length === 0)
    return <p className="text-gray-400 text-sm">No quality metrics yet.</p>

  return (
    <div className="overflow-hidden border border-gray-200 rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
          <tr>
            <th className="px-4 py-2 text-left">Metric</th>
            <th className="px-4 py-2 text-right">Value</th>
            <th className="px-4 py-2 text-right">Threshold</th>
            <th className="px-4 py-2 text-left">Result</th>
            <th className="px-4 py-2 text-left">Detail</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {metrics.map(m => (
            <tr key={m.metric} className={m.pass ? '' : 'bg-red-50'}>
              <td className="px-4 py-2 font-medium font-mono">{m.metric}</td>
              <td className="px-4 py-2 text-right font-mono">{m.value}</td>
              <td className="px-4 py-2 text-right text-gray-500 font-mono">{m.threshold}</td>
              <td className="px-4 py-2">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${m.pass ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {m.pass ? 'PASS' : 'FAIL'}
                </span>
              </td>
              <td className="px-4 py-2 text-gray-500 text-xs">{m.detail ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
