/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        zinc: {
          850: '#1f1f23',
          950: '#09090b',
        },
        // Risk level semantic colors
        critical: {
          DEFAULT: '#dc2626',
          light: '#fef2f2',
          dark: '#991b1b',
        },
        high: {
          DEFAULT: '#ea580c',
          light: '#fff7ed',
          dark: '#9a3412',
        },
        medium: {
          DEFAULT: '#ca8a04',
          light: '#fefce8',
          dark: '#854d0e',
        },
        low: {
          DEFAULT: '#16a34a',
          light: '#f0fdf4',
          dark: '#166534',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

