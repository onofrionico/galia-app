import galiaPreset from '../shared/galia-preset.js'

/** @type {import('tailwindcss').Config} */
export default {
  presets: [galiaPreset],
  content: ['./index.html', './links.html', './cafecitos.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      // Alias históricos de la carta: apuntan a la paleta oficial (ver ../shared/galia-preset.js).
      colors: {
        cream: '#edece4',
        plum: { DEFAULT: '#673b4c', dark: '#52303e', light: '#8a5670' },
        lime: '#cbd159',
        coral: '#dd8c76',
      },
    },
  },
  plugins: [],
}
