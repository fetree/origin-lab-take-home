'use client'
import { useSessions } from '@/hooks/useSessions'
import SessionList from '@/components/SessionList'

export default function HomePage() {
  const { sessions } = useSessions()

  return (
    <main className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-700">Sessions</h2>
        <span className="text-xs text-gray-400">Auto-updates via SSE</span>
      </div>
      <SessionList sessions={sessions} />
    </main>
  )
}
