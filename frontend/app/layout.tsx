import type { Metadata } from 'next'
import { Providers } from '@/components/Providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'RetailVision AI - Store Intelligence Dashboard',
  description: 'Real-time store intelligence and customer analytics platform',
  keywords: ['retail', 'analytics', 'CCTV', 'customer insights', 'store intelligence'],
  authors: [{ name: 'RetailVision AI Team' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
      </head>
      <body className="antialiased">
        <Providers>
          <div id="__next">
            {children}
          </div>
        </Providers>
      </body>
    </html>
  )
}
