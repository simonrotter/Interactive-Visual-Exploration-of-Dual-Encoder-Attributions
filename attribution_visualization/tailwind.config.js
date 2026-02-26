/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],

  theme: {
    extend: {
      colors: {
        active: '#0098FF',
        'active-2': '#007ACC',
        'active-3': '#0065A9',
        'vscode-light': '#F3F3F3',
        vscode: '#444444',
        'vscode-dark': '#252526'
      },
      dropShadow: {
        'md-heavy': '0 4px 3px rgba(0,0,0,0.3)'
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' }
        },
        rotateRight: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(90deg)' }
        },
        rotateLeft: {
          '0%': { transform: 'rotate(90deg)' },
          '100%': { transform: 'rotate(0deg)' }
        },
        slideDownAndFade: {
          from: { opacity: 0, transform: 'translateY(-2px)' },
          to: { opacity: 1, transform: 'translateY(0)' }
        },
        slideLeftAndFade: {
          from: { opacity: 0, transform: 'translateX(2px)' },
          to: { opacity: 1, transform: 'translateX(0)' }
        },
        slideUpAndFade: {
          from: { opacity: 0, transform: 'translateY(2px)' },
          to: { opacity: 1, transform: 'translateY(0)' }
        },
        slideRightAndFade: {
          from: { opacity: 0, transform: 'translateX(-2px)' },
          to: { opacity: 1, transform: 'translateX(0)' }
        }
      },
      animation: {
        'fade-in': 'fade-in 0.1s ease-out',
        'rotate-right': 'rotateRight 0.2s ease-in-out forwards',
        'rotate-left': 'rotateLeft 0.2s ease-in-out forwards',
        slideDownAndFade: 'slideDownAndFade 400ms cubic-bezier(0.16, 1, 0.3, 1)',
        slideLeftAndFade: 'slideLeftAndFade 400ms cubic-bezier(0.16, 1, 0.3, 1)',
        slideUpAndFade: 'slideUpAndFade 400ms cubic-bezier(0.16, 1, 0.3, 1)',
        slideRightAndFade: 'slideRightAndFade 400ms cubic-bezier(0.16, 1, 0.3, 1)'
      }
    }
  },
  plugins: []
}