export type SessionStatus =
  | 'created' | 'uploading' | 'processing' | 'review'
  | 'approved' | 'rejected' | 'failed' | 'paused'

export interface StreamHealth {
  stream: string
  last_seen_at: string | null
  event_count: number
  error_count: number
  bytes_received: number
}

export interface SessionListItem {
  id: string
  game_title: string
  operator_name: string
  resolution: string | null
  fps: number | null
  status: SessionStatus
  streams: string[] | null
  stream_health: StreamHealth[]
  created_at: string
  updated_at: string
}

export interface Session {
  id: string
  game_title: string
  operator_name: string
  resolution: string | null
  fps: number | null
  has_depth: boolean
  status: SessionStatus
  streams: string[] | null
  system_metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
  stream_health: StreamHealth[]
}

export interface StreamEvent {
  id: string
  session_id: string
  stream: string
  seq: number | null
  payload: Record<string, unknown>
  received_at: string
}

export interface Stats {
  total_sessions: number
  by_status: Record<string, number>
  events_per_second: number
  error_rate: number
}
