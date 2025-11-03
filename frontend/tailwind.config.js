/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      screens: {
        'xs': '475px',
        'desktop': '1920px', // For desktop users who want the full experience
      },
      colors: {
        'room': {
          'bg': '#2a2a2a',
          'grid': '#3a3a3a',
          'border': '#4a4a4a',
        },
        'panel': {
          'bg': '#1e1e1e',
          'border': '#333333',
          'text': '#e0e0e0',
        }
      },
      aspectRatio: {
        'room': '4 / 1', // 1920x480 aspect ratio for desktop
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-subtle': 'bounce 2s infinite',
      }
    },
  },
  plugins: [],
}