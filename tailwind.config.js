/** @type {import('tailwindcss').Config} */
export default {
  content: ['./templates/**/*.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'brand-black': 'rgb(15 15 15 / <alpha-value>)',
        'brand-dark-grey': 'rgb(55 55 55 / <alpha-value>)',
        'brand-mid-grey': 'rgb(160 160 160 / <alpha-value>)',
        'brand-light-grey': 'rgb(224 224 224 / <alpha-value>)',
        'brand-bg-grey': 'rgb(248 249 250 / <alpha-value>)',
        'brand-primary': 'var(--brand-primary)',
        'brand-primary-text': 'var(--brand-primary-text)',
        'brand-green': 'rgb(34 197 94 / <alpha-value>)',
        'brand-red': 'rgb(239 68 68 / <alpha-value>)',
        'brand-yellow': 'rgb(234 179 8 / <alpha-value>)',
        'brand-blue': 'rgb(59 130 246 / <alpha-value>)',
      },
    },
  },
  plugins: [],
};
