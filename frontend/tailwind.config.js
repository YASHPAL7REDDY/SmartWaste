/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'matte-black': '#0a0a0a',
        'matte-black-light': '#141414',
        'matte-black-lighter': '#1e1e1e',
        'emerald': '#00d46a',
        'emerald-light': '#34e885',
        'emerald-dark': '#00a852',
        'emerald-glow': 'rgba(0, 212, 106, 0.4)',
        'glass-white': 'rgba(255, 255, 255, 0.05)',
        'glass-white-strong': 'rgba(255, 255, 255, 0.1)',
        'glass-border': 'rgba(255, 255, 255, 0.1)',
        'text-primary': '#ffffff',
        'text-secondary': '#a0a0a0',
        'text-muted': '#666666',
      },
      backdropBlur: {
        'glass': '12px',
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
        'glass-hover': '0 12px 40px rgba(0, 0, 0, 0.4)',
        'emerald-glow': '0 0 20px rgba(0, 212, 106, 0.3)',
        'emerald-glow-strong': '0 0 30px rgba(0, 212, 106, 0.5)',
      },
      borderRadius: {
        'glass': '16px',
        'glass-sm': '12px',
      },
      transitionDuration: {
        'fast': '150ms',
        'normal': '250ms',
        'slow': '350ms',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 212, 106, 0.2)' },
          '50%': { boxShadow: '0 0 30px rgba(0, 212, 106, 0.5)' },
        },
      },
    },
  },
  plugins: [],
}