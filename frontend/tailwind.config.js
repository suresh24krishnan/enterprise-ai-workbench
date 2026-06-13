/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#060d1b',
          900: '#0b1629',
          800: '#122040',
          700: '#1a3056',
        },
      },
    },
  },
  plugins: [],
}
