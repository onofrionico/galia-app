// Guardián del sistema de diseño de Galia: terracota y lima nunca como texto sobre fondos claros.
// Las escalas purple (terracota) solo sirven como texto desde la 700 (>= 5.7:1 sobre crema).
import { describe, it, expect } from 'vitest'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'

const HERE = resolve(process.cwd(), 'src/design')
const ROOTS = [resolve(HERE, '..'), resolve(HERE, '../../../menu-site/src')]
const FORBIDDEN = new RegExp(
  'text-(purple-(50|100|200|300|400|500|600)|galia-coral|galia-lime|coral|lime)(?![A-Za-z0-9_-])',
  'g',
)
// Fondos oscuros (ciruela): ahí el coral y la lima sí contrastan.
const ALLOWED = ['components/layout/Sidebar.jsx', 'pos/layout/PosTopBar.jsx']

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name)
    if (statSync(p).isDirectory()) return name === 'node_modules' ? [] : walk(p)
    return /\.(jsx?|css)$/.test(name) && !name.endsWith('.test.js') ? [p] : []
  })
}

describe('contraste del sistema de diseño', () => {
  it('no hay terracota ni lima como texto fuera de fondos oscuros', () => {
    const offenders = []
    for (const root of ROOTS) {
      for (const file of walk(root)) {
        const rel = relative(root, file).replace(/\\/g, '/')
        if (ALLOWED.includes(rel)) continue
        const hits = readFileSync(file, 'utf8').match(FORBIDDEN)
        if (hits) offenders.push(rel + ': ' + [...new Set(hits)].join(', '))
      }
    }
    expect(offenders).toEqual([])
  })
})
