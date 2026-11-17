# Sistema de diseño de Galia en la app — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el panel admin, el POS, el camarero y la carta pública usen la paleta, tipografía, forma y assets del sistema de diseño oficial de Galia, desde una única fuente de tokens.

**Architecture:** Un preset de Tailwind en `shared/galia-preset.js` define colores, escalas remapeadas, fuentes, radios y las clases `galia-*`. `frontend/` y `menu-site/` lo extienden. Se entrega en dos PRs: (1) tokens, fuentes y contraste; (2) assets y componentes de marca.

**Tech Stack:** Tailwind 3, Vite, React, Vitest 1.6, Flask (solo un default de color). Render construye cada app con `cd <app> && npm run build` desde la raíz del repo, así que `../shared/` está disponible en el build.

**Spec:** `docs/superpowers/specs/2026-11-17-sistema-diseno-galia-design.md`
**Fuente de verdad del diseño:** artifact "Galia" https://claude.ai/artifact/DVadrPwPoMSXDUZxmVWvbi (`project/tokens.json`, `project/README.md`, `project/components/bundle.css`, grupos de assets).

## Global Constraints

- Ciruela `#673b4c`, terracota `#dd8c76`, lima `#cbd159`, crema `#edece4`, arena `#d1cdba` y `#e1ded0`, blanco `#ffffff`, ciruela atenuada `#673b4ccc`.
- Fuentes: `Anton` (títulos) y `Poppins` 300/400/500/700 (texto). DM Sans se elimina.
- Radios: `galia-lg` 24px, `galia-sm` 6px, `pill` 999px. Solo carta, login, tarjetas destacadas del Dashboard y clases `galia-*`; el admin denso, el POS y el camarero mantienen sus radios.
- Terracota y lima nunca como texto sobre crema. Texto ≥ 4.5:1 (≥ 3:1 a 24px o más).
- No hardcodear colores de marca por pantalla: salen del preset o de `constants/colors.js`.
- No se tocan migraciones ni los tags de carta ya guardados en la base.
- Ramas desde `origin/main` actualizado; mergear `main` antes de abrir cada PR. Worktree: `C:\Users\onofr\Desktop\galia-design-system`, rama `feature/design-system`.
- Commits terminan con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; descripciones de PR con `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

## Review Focus

1. Nombre de producto largo o precio de 6+ dígitos (`$125000`) en la pastilla: no debe romper la grilla de la carta en celular.
2. Camarero offline (PWA): si Google Fonts no carga, el texto debe caer en `system-ui` sin romper el layout.
3. Pantallas que usan `text-purple-*` sobre fondo oscuro (sidebar, barra POS): ahí el coral sí tiene contraste y no debe cambiarse a ciruela.
4. Tags de carta existentes con `#5C2E46`: siguen mostrándose bien; solo cambia el default de los nuevos.
5. Clases `galia-*` generadas dinámicamente: no deben purgarse (Tailwind las ve en `@layer components` del preset, no en strings armados).

---

## PR 1 — Tokens y tipografía

### Task 1: Preset compartido con tokens y test de contraste

**Files:**
- Create: `shared/galia-tokens.js`, `shared/galia-preset.js`, `shared/galia-tokens.test.js`
- Modify: `menu-site/package.json` (agregar script `"test:shared": "vitest run ../shared"` solo si el `vitest` de `menu-site` no recoge `../shared`; el builder elige)

**Interfaces:**
- Produces: `shared/galia-tokens.js` exporta `GALIA_COLORS` (`{ plum, terracotta, lime, cream, sand100, sand200, white }` en hex), `contrastRatio(fg: string, bg: string): number`. `shared/galia-preset.js` exporta por defecto un preset de Tailwind con `theme.extend.colors.galia`, `blue`/`rose` (escala plum), `purple` (escala terracota), `gray` (stone, sin cambios), `fontFamily.sans/display`, `borderRadius['galia-lg'|'galia-sm'|'pill']` y un `plugins: [plugin(...)]` que registra las clases `galia-price`, `galia-label`, `galia-banner`, `galia-sticker`, `galia-divider`, `galia-card` (mismos valores que `components/bundle.css` del sistema).

- [ ] **Step 1: Test `shared/galia-tokens.test.js` (falla)** con estas aserciones: `GALIA_COLORS.plum === '#673b4c'` y el resto de la paleta con sus hex exactos; `contrastRatio(plum, cream) >= 7.5`; `contrastRatio(plum, white) >= 9`; `contrastRatio(plum, lime) >= 5.5`; `contrastRatio(plum, sand100) >= 6.5`; `contrastRatio(terracotta, cream) < 3` (documenta que no es texto); el preset tiene `theme.extend.colors.blue[700] === GALIA_COLORS.plum`.
- [ ] **Step 2:** `cd menu-site && npx vitest run ../shared` → FAIL (módulo inexistente).
- [ ] **Step 3: Implementar** `galia-tokens.js` (paleta + `contrastRatio` con luminancia relativa WCAG) y `galia-preset.js`. La escala plum 50–950 se deriva con `700 = #673b4c`, `600` un paso más claro, `800–950` más oscuros; la escala terracota con `400 = #dd8c76`. Dejar un comentario con la tabla de la escala.
- [ ] **Step 4:** correr el test → PASS.
- [ ] **Step 5: Commit** `feat(diseno): preset compartido con tokens oficiales de Galia`.

### Task 2: Conectar el preset y cambiar las fuentes

**Files:**
- Modify: `frontend/tailwind.config.js`, `menu-site/tailwind.config.js`, `frontend/src/index.css`, `menu-site/src/index.css`, `frontend/index.html`, `menu-site/index.html`, `menu-site/links.html`, `menu-site/cafecitos.html`

**Interfaces:**
- Consumes: `shared/galia-preset.js` de la Task 1.
- Produces: clases `font-sans`/`font-body` = Poppins, `font-display` = Anton; variables shadcn de `frontend/src/index.css` en la paleta oficial.

- [ ] **Step 1:** en ambos `tailwind.config.js`, `presets: [galiaPreset]` y borrar las definiciones duplicadas de colores y fuentes. En `menu-site` conservar los alias `cream`, `plum`, `lime`, `coral` (apuntan a los nuevos valores) para no tocar los 12 archivos que los usan; `coral` = terracota.
- [ ] **Step 2:** en los 4 HTML, reemplazar el `<link>` de Google Fonts por `family=Anton&family=Poppins:wght@300;400;500;700&display=swap`.
- [ ] **Step 3:** recalcular las variables HSL de `:root` en `frontend/src/index.css` desde la paleta (`--background` crema, `--foreground` y `--primary`/`--ring` ciruela, `--secondary/--muted/--accent` arena clara, `--border/--input` derivados de arena). `.dark` no se toca. `menu-site/src/index.css`: `font-body` ya apunta a Poppins vía preset.
- [ ] **Step 4:** `cd frontend && npm run build` y `cd menu-site && npm run build` → ambos OK; `grep -rn "DM Sans" frontend menu-site --include=*.html --include=*.js --include=*.css --exclude-dir=node_modules --exclude-dir=dist` → sin resultados.
- [ ] **Step 5: Commit** `feat(diseno): Anton + Poppins y paleta oficial en admin y carta`.

### Task 3: Paleta vieja del POS y colores sueltos

**Files:**
- Modify: `frontend/src/constants/colors.js`, `frontend/src/pos/layout/PosTopBar.jsx`, `backend/app/models/menu.py:146`, `backend/app/routes/menu.py:464`, `frontend/src/components/menu/MenuSettingsPanel.jsx:48,73`, `menu-site/src/cafecitos/CafecitosApp.jsx:108`
- Test: `frontend/src/constants/colors.test.js`

**Interfaces:**
- Consumes: `GALIA_COLORS` de `shared/galia-tokens.js`.
- Produces: `GALIA` en `colors.js` con las mismas claves que hoy (`amarillo`, `marron`, `crema`, `blanco`, `grisClaro`, `grisLigero`, `verde`) pero valores oficiales (`amarillo = lime`, `marron = plum`, `crema = cream`).

- [ ] **Step 1: Test `colors.test.js` (falla):** `GALIA.marron === GALIA_COLORS.plum`, `GALIA.amarillo === GALIA_COLORS.lime`, `GALIA.crema === GALIA_COLORS.cream`.
- [ ] **Step 2:** correr → FAIL. **Step 3:** `colors.js` importa de `../../../shared/galia-tokens.js`; si `PosTopBar` usa `GALIA.*`, queda coherente sin cambios de markup.
- [ ] **Step 4:** default de tag `#673b4c` en `models/menu.py`, `routes/menu.py` y `MenuSettingsPanel.jsx`; color oscuro del QR `#673b4c` en `CafecitosApp.jsx`. Sin migración: el default de la columna en Python no altera filas existentes.
- [ ] **Step 5:** `cd frontend && npx vitest run` y `cd backend && python -m pytest tests -q -k menu` → PASS. **Commit** `feat(diseno): POS y colores por defecto con la paleta oficial`.

### Task 4: Auditoría de contraste (coral/lima como texto)

**Files:**
- Create: `frontend/src/design/contrast.guard.test.js`
- Modify: los archivos con `text-purple-*` (35 usos en 17 archivos de `frontend/src`: `ExpenseClassifierModal`, `CreateScheduleModal`, `MLRecommendations`, `Dashboard`, `ExpenseCategories`, `Expenses`, `HolidaysPage`, `JobPositions`, `MLDashboard`, `MyPayrollDetail`, `Payroll`, `PayrollDetail`, `Products`, `Reports`, `Sales`, `Stock`, `TimeTracking`) y los 2 usos de `text-galia-coral|lime`.

**Interfaces:**
- Produces: un test guardián que recorre `frontend/src` y `menu-site/src` y falla si encuentra `text-purple-`, `text-galia-coral`, `text-galia-lime`, `text-coral` o `text-lime` fuera de un allowlist explícito (`ALLOWED = ['components/layout/Sidebar.jsx', 'pos/layout/PosTopBar.jsx']`: fondos oscuros, donde el coral sí contrasta).

- [ ] **Step 1: escribir el guardián (falla)** con la lista de hallazgos actual.
- [ ] **Step 2:** correr → FAIL listando archivos.
- [ ] **Step 3:** por cada uso, decidir: texto sobre fondo claro → `text-blue-700` (ciruela) o `text-gray-700`; badge con fondo coral → `bg-purple-100 text-blue-700`. Los íconos decorativos de ≥ 24px pueden quedar en coral. Fondos oscuros: agregar al allowlist con comentario.
- [ ] **Step 4:** guardián → PASS; `npm run build` OK.
- [ ] **Step 5: Commit** `fix(diseno): sin coral ni lima como texto sobre fondos claros`.

### Task 5: Verificación y PR 1

- [ ] **Step 1:** `git fetch origin && git merge origin/main`; correr `npx vitest run` en `frontend/` y `menu-site/`, ambos builds y `pytest` del backend.
- [ ] **Step 2:** levantar `frontend` (dev) y `menu-site` y revisar con capturas: Login, Dashboard, Empleados, Horarios, Ventas, Productos, Recetas, Carta (admin), POS caja/mostrador/camarero, carta pública, `/links` y `/cafecitos`. Anotar cualquier texto ilegible o resto de la paleta vieja.
- [ ] **Step 3:** abrir PR 1 con las capturas; no mergear sin que el usuario lo pida.

---

## PR 2 — Capa de marca (rama nueva desde `main` con PR 1 mergeado)

### Task 6: Assets oficiales y presupuesto de peso

**Files:**
- Create: `frontend/public/brand/` y `menu-site/public/brand/` con `logo-ciruela.png`, `logo-crema.png`, `simbolo-ciruela.png`, `flor-lima.png`, `flor-terracota.png`; `ilustraciones/{cafetera-flores,tazas-apiladas,torta-terracota,granos-de-cafe,patron-cuadrille}.svg`; `scripts/optimize-brand-assets.mjs`
- Test: `frontend/src/design/brandAssets.test.js`

**Interfaces:**
- Produces: tabla de rutas públicas `/brand/...` usada por las Tasks 7 y 8; test que falla si algún archivo de `public/brand/ilustraciones/` pesa más de 120 KB o si falta alguno de los logos listados.

- [ ] **Step 1: test (falla)** que verifica existencia y peso máximo de los archivos listados.
- [ ] **Step 2:** logos: descargar de Drive *Formales/Logos fondo Transp* las variantes en la paleta oficial (vertical completo, símbolo, crema sobre ciruela). Si el conector de Drive no puede acceder, **detenerse y pedir los archivos al usuario**; no usar los del artifact (ciruela magenta).
- [ ] **Step 3:** ilustraciones: leer del artifact con `Artifact read` y `path` = id del blob (ids en `project/design-system.json`, `assetGroups.Ilustraciones.files`). Optimizar con `svgo` (devDependency, script `scripts/optimize-brand-assets.mjs`) hasta cumplir el presupuesto; si una no baja de 120 KB, usarla solo en la carta o descartarla.
- [ ] **Step 4:** test → PASS. **Commit** `feat(diseno): logos e ilustraciones oficiales optimizados`.

### Task 7: Componentes `galia-*` en la carta pública

**Files:**
- Modify: `menu-site/src/components/MenuItem.jsx`, `CategorySection.jsx`, `GroupSection.jsx`, `Header.jsx`, `Footer.jsx`, `TagFilters.jsx`, `menu-site/src/index.css`
- Test: `menu-site/src/lib/priceFormat.test.js` (solo si se extrae un helper de formato de precio; si no, sin test unitario)

**Interfaces:**
- Consumes: clases `galia-price`, `galia-label`, `galia-banner`, `galia-divider`, `galia-card` del preset.

- [ ] **Step 1:** `MenuItem`: precio en `galia-price`; con 2+ variantes, cada precio en su pastilla. Sin `whitespace-nowrap` extra en el contenedor para que un nombre largo envuelva sin empujar la pastilla.
- [ ] **Step 2:** `CategorySection` con título `font-display` en `galia-banner`; `galia-divider` (punteado terracota) entre ítems; `galia-card` solo para bloques de combos si existen.
- [ ] **Step 3:** `Header`/`Footer`: logo oficial de la Task 6, lema "Hay lugar para todos" en el footer.
- [ ] **Step 4:** `npx vitest run` y `npm run build` OK; verificar en celular (viewport 375px): nombres largos y precios de 6 dígitos no rompen la grilla.
- [ ] **Step 5: Commit** `feat(carta): pastillas de precio, carteles y divisores del sistema de diseño`.

### Task 8: Login, estados vacíos, sidebar y navbar

**Files:**
- Modify: `frontend/src/pages/Login.jsx:41`, `frontend/src/components/layout/Sidebar.jsx`, `Navbar.jsx`
- Create: `frontend/src/components/common/EmptyState.jsx`
- Modify: las listas que hoy muestran "No hay…" en texto plano (el builder identifica las 5–8 más visitadas: Empleados, Productos, Gastos, Ventas, Recetas, Proveedores).

**Interfaces:**
- Produces: `EmptyState({ title: string, hint?: string, illustration?: 'cafetera' | 'tazas' | 'torta' | 'granos' })` — imagen desde `/brand/ilustraciones/`, `alt=""` decorativa, texto en Poppins.

- [ ] **Step 1:** `Login`: logo oficial centrado, tarjeta con `rounded-galia-lg`, ilustración `cafetera-flores` decorativa (`aria-hidden`), botón ciruela.
- [ ] **Step 2:** `Sidebar`/`Navbar`: logo oficial crema sobre ciruela; flor lima oficial para el ítem activo.
- [ ] **Step 3:** `EmptyState` y reemplazo en las listas elegidas, con imagen `loading="lazy"`.
- [ ] **Step 4:** `npx vitest run`, `npm run lint`, `npm run build` OK.
- [ ] **Step 5: Commit** `feat(diseno): login, estados vacíos y marco con identidad oficial`.

### Task 9: Favicons, manifest y PR 2

**Files:**
- Modify: `frontend/public/` (favicons, `android-chrome-*`, `apple-touch-icon.png`, `site.webmanifest` con `theme_color`/`background_color` oficiales), `menu-site/public/brand/favicon.png`

- [ ] **Step 1:** regenerar los íconos desde el símbolo oficial (ciruela sobre crema) en 16, 32, 180, 192 y 512 px; actualizar `theme_color` a `#673b4c` y `background_color` a `#edece4`.
- [ ] **Step 2:** `git merge origin/main`; tests y builds de `frontend/`, `menu-site/` y `backend/`.
- [ ] **Step 3:** repetir la revisión visual de la Task 5 y comparar contra las capturas del PR 1.
- [ ] **Step 4:** abrir PR 2 con capturas antes/después; no mergear sin que el usuario lo pida.
