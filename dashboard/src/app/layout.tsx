import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Session Monitor',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-lg font-semibold tracking-tight">Session Monitor</h1>
        </header>
        {children}
      </body>
    </html>
  )
}
