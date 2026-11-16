/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'sk-bg': '#F8FAF5',
        'sk-primary': '#2D6A4F',
        'sk-secondary': '#52B788',
        'sk-accent': '#74C69D',
        'sk-text': '#1B2D1E',
        'sk-text-secondary': '#4A6B50',
        'sk-border': '#D8E8DC',
        'sk-card': '#FFFFFF',
        'sk-success': '#40916C',
        'sk-warning': '#F4A261',
        'sk-error': '#E63946',
        'sk-info': '#457B9D',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0,0,0,0.07), 0 1px 2px -1px rgba(0,0,0,0.05)',
        'card-hover': '0 4px 12px 0 rgba(45,106,79,0.12)',
      }
    },
  },
  plugins: [],
}
