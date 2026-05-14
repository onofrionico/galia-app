// frontend/src/constants/colors.js

export const GALIA = {
  amarillo: '#D4E157',      // Primary accent
  marron: '#6B4C5C',        // Secondary/brand
  crema: '#E8DCC4',         // Main background
  blanco: '#FFFBF8',        // Card/overlay background
  grisSecondary: '#8A8A8A', // Secondary text, disabled states
  grisBorder: '#E5E5E5',    // Borders, dividers, subtle separators
  verde: '#7CB342',         // Status: Libre
}

// Tailwind color utility object for config extension (optional for later)
export const galiaTailwind = {
  'galia-amarillo': GALIA.amarillo,
  'galia-marron': GALIA.marron,
  'galia-crema': GALIA.crema,
  'galia-blanco': GALIA.blanco,
  'galia-gris-secondary': GALIA.grisSecondary,
  'galia-gris-border': GALIA.grisBorder,
  'galia-verde': GALIA.verde,
}

export default GALIA
