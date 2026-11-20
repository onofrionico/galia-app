// frontend/src/constants/colors.js
// Paleta oficial de Galia: viene de shared/galia-tokens.js (sistema de diseño).
import { GALIA_COLORS } from '../../../shared/galia-tokens.js'

export const GALIA = {
  amarillo: GALIA_COLORS.lime,       // Primary accent
  marron: GALIA_COLORS.plum,         // Secondary/brand
  crema: GALIA_COLORS.cream,         // Main background
  blanco: GALIA_COLORS.white,        // Card/overlay background
  grisClaro: '#8A8A8A',              // Secondary text
  grisLigero: '#E5E5E5',             // Borders
  verde: '#7CB342',                  // Status: Libre
}

export const galiaTailwind = {
  'galia-amarillo': GALIA.amarillo,
  'galia-marron': GALIA.marron,
  'galia-crema': GALIA.crema,
  'galia-blanco': GALIA.blanco,
  'galia-gris-claro': GALIA.grisClaro,
  'galia-gris-ligero': GALIA.grisLigero,
  'galia-verde': GALIA.verde,
}

export default GALIA
