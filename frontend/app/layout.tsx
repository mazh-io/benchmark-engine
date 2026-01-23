/**
 * Root Layout
 * 
 * Global layout wrapper for the entire application.
 * Includes metadata, fonts, providers, and global styles.
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { QueryClientProvider } from '@/components/providers/QueryClientProvider';
import '@/styles/globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'AI Benchmark Dashboard | Real-time Performance Metrics',
  description: 'Compare AI provider performance metrics including speed (TTFT), stability (jitter), and value scores. Real-time benchmarks for OpenAI, Anthropic, Groq, and more.',
  keywords: [
    'AI benchmarks',
    'LLM performance',
    'API speed comparison',
    'OpenAI vs Anthropic',
    'AI provider metrics',
    'TTFT',
    'latency monitoring',
  ],
  authors: [{ name: 'Benchmark Engine' }],
  openGraph: {
    title: 'AI Benchmark Dashboard',
    description: 'Real-time AI provider performance metrics',
    type: 'website',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  themeColor: '#0A0E14',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="antialiased">
        <QueryClientProvider>
          {children}
        </QueryClientProvider>
      </body>
    </html>
  );
}

