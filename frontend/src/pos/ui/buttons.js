const BASE = 'inline-flex items-center justify-center gap-2 rounded-lg px-4 min-h-[44px] font-medium transition-colors ' +
  'disabled:cursor-not-allowed disabled:opacity-40'

const VARIANTS = {
  primary: 'bg-galia-plum text-galia-cream hover:bg-galia-plum-dark',
  secondary: 'border border-gray-300 bg-white text-gray-800 hover:bg-gray-50',
  danger: 'border border-red-300 bg-white text-red-700 hover:bg-red-50',
  ghost: 'text-gray-700 hover:bg-gray-100',
}

export const btn = (variant = 'secondary', extra = '') => `${BASE} ${VARIANTS[variant]} ${extra}`
