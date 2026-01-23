import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Acid Theme Colors
        'acid-bg': '#0A0E14',
        'acid-surface': '#1A1F29',
        'acid-surface-hover': '#252B37',
        'acid-border': '#2D3748',
        'acid-text': '#E2E8F0',
        'acid-text-muted': '#94A3B8',
        'acid-primary': '#3B82F6',
        'acid-success': '#10B981',
        'acid-warning': '#F59E0B',
        'acid-danger': '#EF4444',
        'acid-accent': '#8B5CF6',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['Consolas', 'Monaco', 'monospace'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s infinite linear',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
