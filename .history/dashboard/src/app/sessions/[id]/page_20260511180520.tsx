'use client'
import Link from 'next/link'
import { useSessionDetail } from '@/hooks/useSessionDetail'
import StreamHealthGrid from '@/components/StreamHealthGrid'
import EventTimeline from '@/components/EventTimeline'
import QualityMetrics from '@/components/QualityMetrics'

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

function MetadataValue({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span className="text-gray-400">—</span>
  if (typeof value === 'object')
    return (
      <div className="pl-3 border-l border-gray-200 space-y-1 mt-1">
        {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
          <div key={k} className="flex gap-2">
            <span className="text-gray-500 flex-shrink-0">{k}:</span>
            <MetadataValue value={v} />
          </div>
        ))}
      </div>
    )
  return <span className="text-gray-800 font-mono">{String(value)}</span>
}

function FailureBanner({ status, events }: { status: string; events: import('@/types').StreamEvent[] }) {
  if (status === 'rejected') {
    const review = events.find(e => e.stream === 'review' && (e.payload as Record<string, unknown>).decision === 'rejected')
    const reason = review ? (review.payload as Record<string, unknown>).reason as string : null
    const category = review ? (review.payload as Record<string, unknown>).rejection_category as string : null
    if (!reason) return null
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
        <span className="font-semibold text-red-700">Rejected{category ? ` · ${category}` : ''}: </span>
        <span className="text-red-600">{reason}</span>
      </div>
    )
  }
  if (status === 'failed') {
    const transcode = events.find(e => e.stream === 'transcode' && (e.payload as Record<string, unknown>).stage === 'failed')
    const error = transcode ? (transcode.payload as Record<string, unknown>).error as string : null
    console.log(transcode)
    if (!error) return null
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
        <span className="font-semibold text-red-700">Pipeline failure: </span>
        <span className="text-red-600 font-mono">{error}</span>
      </div>
    )
  }
  return null
}

interface Props { params: { id: string } }

export default function SessionDetailPage({ params }: Props) {
  const { id } = params
  const { session, events } = useSessionDetail(id)

  if (!session) {
    return (
      <main className="p-6">
        <div className="text-gray-400 animate-pulse">Loading session…</div>
      </main>
    )
  }

  return (
    <main className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link href="/" className="text-gray-400 hover:text-gray-600 mt-1">← Back</Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-xl font-semibold">{session.game_title}</h2>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[session.status] ?? 'bg-gray-100'}`}>
              {session.status}
            </span>
          </div>
          <p className="text-gray-500 text-sm mt-1">
            {session.operator_name} · {session.resolution ?? '?'} @ {session.fps ?? '?'}fps
            {session.has_depth ? ' · depth' : ''}
          </p>
        </div>
      </div>

      <FailureBanner status={session.status} events={events} />

      {/* System Metadata */}
      {session.system_metadata && (
        <section>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">System Metadata</h3>
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-xs space-y-1">
            {Object.entries(session.system_metadata).map(([k, v]) => (
              <div key={k} className="flex gap-2">
                <span className="text-gray-500 flex-shrink-0 w-36">{k}</span>
                <MetadataValue value={v} />
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Stream Health */}
      <section>
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Stream Health
          <span className="ml-2 text-gray-400 normal-case font-normal">live</span>
        </h3>
        <StreamHealthGrid health={session.stream_health} sessionStatus={session.status} />
      </section>

      {/* Quality Metrics */}
      <section>
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Quality Metrics</h3>
        <QualityMetrics events={events} />
      </section>

      {/* Event Timeline */}
      <section>
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Event Timeline
          <span className="ml-2 text-gray-400 normal-case font-normal">{events.length} events (newest first)</span>
        </h3>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <EventTimeline events={events} />
        </div>
      </section>
    </main>
  )
}
