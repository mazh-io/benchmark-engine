import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { QueryClientProvider } from '@/templates/providers/QueryClientProvider';
import '@/styles/globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'MAZH',
  description: 'Real-time AI provider benchmarks',
  themeColor: '#000000',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-black min-h-screen antialiased">
        <QueryClientProvider>{children}</QueryClientProvider>
      </body>
    </html>
  );
}
