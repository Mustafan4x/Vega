import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          '50': 'var(--color-primary-50)',
          '500': 'var(--color-primary-500)',
          DEFAULT: 'var(--color-primary-500)',
          soft: 'var(--color-primary-soft)',
        },
        accent: {
          '500': 'var(--color-accent-500)',
          DEFAULT: 'var(--color-accent-500)',
        },
        success: {
          '500': 'var(--color-success-500)',
          DEFAULT: 'var(--color-success-500)',
        },
        danger: {
          '500': 'var(--color-danger-500)',
          DEFAULT: 'var(--color-danger-500)',
        },
        info: {
          '500': 'var(--color-info-500)',
          DEFAULT: 'var(--color-info-500)',
        },
        background: 'var(--color-background)',
        surface: 'var(--color-surface)',
        'surface-2': 'var(--color-surface-2)',
        border: 'var(--color-border)',
        fg: 'var(--color-text-primary)',
        'fg-muted': 'var(--color-text-muted)',
        'fg-subtle': 'var(--color-text-subtle)',
      },
      fontFamily: {
        sans: ['Manrope', 'Inter', 'system-ui', 'sans-serif'],
        display: ['IBM Plex Serif', 'Georgia', 'serif'],
        number: ['Newsreader', 'Iowan Old Style', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'Menlo', 'monospace'],
      },
      borderRadius: {
        sm: '3px',
        md: '6px',
        lg: '10px',
        card: '6px',
        pill: '999px',
      },
    },
  },
  plugins: [],
}

export default config
