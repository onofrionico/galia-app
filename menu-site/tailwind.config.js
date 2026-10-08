/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        cream: '#F5F1EA',
        plum: { DEFAULT: '#5C2E46', dark: '#43203A', light: '#8A5A72' },
        lime: '#C5D94A',
        coral: '#E0866A',
      },
      fontFamily: {
        display: ['Anton', 'Impact', 'sans-serif'],
        body: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
