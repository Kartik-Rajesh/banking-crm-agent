/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        crm: {
          base:    'var(--bg-base)',
          surface: 'var(--bg-surface)',
          raised:  'var(--bg-elevated)',
          border:  'var(--border)',
          blue:    'var(--accent-primary)',
          green:   'var(--accent-success)',
          amber:   'var(--accent-warning)',
          red:     'var(--accent-danger)',
          purple:  'var(--accent-purple)',
          p1:      'var(--text-primary)',
          p2:      'var(--text-secondary)',
          p3:      'var(--text-tertiary)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'fade-in':  'fadeIn 0.25s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
        'fill-bar': 'fillBar 600ms ease-out both',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { transform: 'translateY(6px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',   opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
