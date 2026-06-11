'use client'

import { DashboardPage } from '@/components/DashboardPage'

// Configuration - update with actual backend URLs
const CONFIG = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  wsBaseUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  apiKey: process.env.NEXT_PUBLIC_API_KEY || 'demo-key-12345',
}

export default function Home() {
  return (
    <DashboardPage
      apiBaseUrl={CONFIG.apiBaseUrl}
      wsBaseUrl={CONFIG.wsBaseUrl}
      apiKey={CONFIG.apiKey}
    />
              </p>
            </div>
          ))}
        </div>

        {/* Status */}
        <div className="mt-12 p-4 bg-white rounded-lg shadow-md">
          <p className="text-green-600 font-semibold mb-2">✓ System Status: Ready</p>
          <p className="text-gray-600 text-sm">
            Dashboard under construction - Phase 1 complete
          </p>
        </div>
      </div>
    </main>
  )
}
