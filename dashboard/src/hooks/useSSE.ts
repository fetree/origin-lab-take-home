'use client'
import { useEffect, useRef } from 'react'

export function useSSE(url: string, onMessage: (data: unknown) => void): void {
  const cbRef = useRef(onMessage)
  cbRef.current = onMessage

  useEffect(() => {
    let es: EventSource
    let retryTimer: ReturnType<typeof setTimeout>

    function connect() {
      es = new EventSource(url)
      es.onmessage = (e: MessageEvent<string>) => {
        try { cbRef.current(JSON.parse(e.data)) } catch { /* ignore malformed */ }
      }
      es.onerror = () => {
        es.close()
        retryTimer = setTimeout(connect, 3000)
      }
    }

    connect()
    return () => { es?.close(); clearTimeout(retryTimer) }
  }, [url])
}
