import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Montserrat', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        aurora: {
          green: '#00FF87',
          blue: '#0A1628',
          frost: '#E8F4F8',
          violet: '#7B2FBE',
          cyan: '#00D4FF',
          pink: '#FF6EC7',
          snow: '#FAFBFC',
          midnight: '#050B1A',
        },
        primary: {
          DEFAULT: '#00FF87',
          hover: '#00CC6C',
          light: '#66FFB5',
        },
        surface: {
          DEFAULT: '#FAFBFC',
          alt: '#E8F4F8',
          dark: '#0A1628',
          deeper: '#050B1A',
        },
        border: {
          DEFAULT: '#E2E8F0',
          light: '#F1F5F9',
        },
        text: {
          primary: '#0A1628',
          secondary: '#475569',
          muted: '#94A3B8',
          inverse: '#FAFBFC',
        },
      },
      borderRadius: {
        DEFAULT: '0.5rem',
      },
      boxShadow: {
        card: '0 2px 12px rgba(0,0,0,0.06)',
        cardHover: '0 4px 20px rgba(0,0,0,0.10)',
        button: '0 2px 8px rgba(0,255,135,0.3)',
      },
      animation: {
        'fade-in': 'fadeIn 480ms ease-out',
        'slide-up': 'slideUp 480ms ease-out',
        shimmer: 'shimmer 2s infinite linear',
        'aurora-pulse': 'auroraPulse 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        auroraPulse: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

export default config
