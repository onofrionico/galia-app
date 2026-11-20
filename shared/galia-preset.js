// Preset de Tailwind con el sistema de diseño de Galia. Lo extienden frontend/ y menu-site/.
import { GALIA_COLORS as C } from './galia-tokens.js'

// Escala plum (reemplaza blue y rose: el código usa ~500 clases *-blue-* para acciones/primario).
// 700 es la ciruela oficial; 600 un paso más claro; 800-950 más oscuros.
const plum = {
  50: '#faf4f7', 100: '#f3e6ec', 200: '#e3c9d6', 300: '#c795ab', 400: '#a0647f',
  500: '#8a5670', 600: '#77465c', 700: C.plum, 800: '#52303e', 900: '#3b2230', 950: '#261520',
}

// Escala terracota (reemplaza purple: el código usa *-purple-* para acentos). 400 es el terracota oficial.
const terracotta = {
  50: '#fdf4f1', 100: '#fbe6df', 200: '#f6cbbd', 300: '#eaa995', 400: C.terracotta,
  500: '#cf6f55', 600: '#b6553a', 700: '#934430', 800: '#74372a', 900: '#5c2e25', 950: '#33160f',
}

// Neutro cálido (stone de Tailwind).
const gray = {
  50: '#fafaf9', 100: '#f5f5f4', 200: '#e7e5e4', 300: '#d6d3d1', 400: '#a8a29e',
  500: '#78716c', 600: '#57534e', 700: '#44403c', 800: '#292524', 900: '#1c1917', 950: '#0c0a09',
}

// Clases del sistema (components/bundle.css), con los mismos valores.
function galiaComponents({ addComponents }) {
  addComponents({
    '.galia-price': {
      display: 'inline-block', fontSize: '13px', lineHeight: '18px', fontWeight: '400',
      color: C.plum, backgroundColor: C.white, borderRadius: '999px', padding: '0 8px', whiteSpace: 'nowrap',
    },
    '.galia-label': {
      display: 'inline-block', fontSize: '10px', lineHeight: '14px', letterSpacing: '0.4px',
      textTransform: 'uppercase', color: C.cream, backgroundColor: C.plum, borderRadius: '999px', padding: '1px 8px',
    },
    '.galia-banner': {
      display: 'inline-block', padding: '8px 32px', borderRadius: '24px 24px 0 0', backgroundColor: C.lime, color: C.plum,
    },
    '.galia-sticker': {
      display: 'inline-block', fontFamily: 'Anton, Impact, sans-serif', fontSize: '18px', lineHeight: '1.2',
      color: C.cream, backgroundColor: C.plum, borderRadius: '6px', padding: '4px 8px', transform: 'rotate(-2deg)',
    },
    '.galia-divider': { border: '0', borderTop: `2px dotted ${C.terracotta}`, margin: '16px 0' },
    '.galia-card': { backgroundColor: C.white, borderRadius: '24px', padding: '24px' },
  })
}

export default {
  theme: {
    extend: {
      colors: {
        blue: plum,
        rose: plum,
        purple: terracotta,
        gray,
        galia: {
          cream: C.cream,
          plum: C.plum,
          'plum-dark': '#52303e',
          'plum-light': '#8a5670',
          lime: C.lime,
          coral: C.terracotta,
          sand: C.sand100,
          'sand-dark': C.sand200,
        },
      },
      fontFamily: {
        sans: ['Poppins', 'system-ui', 'sans-serif'],
        body: ['Poppins', 'system-ui', 'sans-serif'],
        display: ['Anton', 'Impact', 'sans-serif'],
      },
      borderRadius: { 'galia-lg': '24px', 'galia-sm': '6px', pill: '999px' },
    },
  },
  // Función simple (sin importar tailwindcss/plugin) para que shared/ no dependa de node_modules.
  plugins: [galiaComponents],
}
