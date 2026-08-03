/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Sora', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        // EcoBiome Night palette — deep ocean teal/amber
        night: {
          950: '#050b14',
          900: '#0a1620',
          850: '#0e1c28',
          800: '#13242f',
          700: '#1b3140',
          600: '#264456',
          500: '#355a70',
        },
        teal: {
          50: '#ecfdf6',
          100: '#d1faec',
          200: '#a7f3d9',
          300: '#6ee7c0',
          400: '#34d3a4',
          500: '#10b888',
          600: '#05946b',
          700: '#047556',
          800: '#065d46',
          900: '#064c3b',
        },
        amber: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        coral: {
          400: '#fb7185',
          500: '#f43f5e',
          600: '#e11d48',
          700: '#be123c',
        },
        ok: {
          400: '#34d3a4',
          500: '#10b888',
          600: '#05946b',
        },
        warn: {
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
        },
        crit: {
          400: '#fb7185',
          500: '#f43f5e',
          600: '#e11d48',
        },
      },
      boxShadow: {
        glow: '0 0 24px -4px rgba(16, 184, 136, 0.25)',
        'glow-amber': '0 0 24px -4px rgba(245, 158, 11, 0.25)',
        'glow-coral': '0 0 24px -4px rgba(244, 63, 94, 0.25)',
        card: '0 1px 3px rgba(0,0,0,0.3), 0 0 1px rgba(0,0,0,0.4)',
        'card-hover': '0 8px 32px -8px rgba(0,0,0,0.5), 0 0 1px rgba(0,0,0,0.4)',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'wave': 'wave 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        wave: {
          '0%, 100%': { transform: 'translateY(0) scaleY(1)' },
          '50%': { transform: 'translateY(-4px) scaleY(1.02)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
};
