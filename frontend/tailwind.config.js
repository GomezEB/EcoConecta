/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: { colors: { eco: { 50: '#edfaf0', 100: '#d9f3df', 500: '#259b50', 700: '#166c38', 900: '#153e26' } } },
  },
  plugins: [],
}
