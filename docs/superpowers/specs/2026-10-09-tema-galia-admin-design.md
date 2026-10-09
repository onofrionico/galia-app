# Tema Galia en el panel admin — Diseño

**Fecha:** 2026-10-09
**Estado:** Aprobado en brainstorming

## Objetivo
Aplicar al panel admin (`frontend/`) la identidad visual de la carta pública (`menu-site/`): crema, bordó, lima y coral; DM Sans + Anton; logo y flores. Sin rediseñar el layout de cada pantalla.

## Decisiones
| Tema | Decisión |
|---|---|
| Alcance | Tema global vía Tailwind (no pantalla por pantalla) |
| Sidebar | Bordó oscuro, texto crema, logo arriba, ítem activo con flor lima |
| Colores semánticos | Rojo/verde/ámbar/amarillo se mantienen; violeta pasa a coral y rosa a bordó |
| Títulos | Anton sólo en `h1` de cada pantalla; resto DM Sans |

## 1. Paleta (frontend/tailwind.config.js → theme.extend.colors)
- `blue` se redefine como escala bordó (el código usa ~500 clases `*-blue-*` para acciones/primario):
  `50 #FAF3F6, 100 #F2E4EB, 200 #E0C4D2, 300 #C08DA6, 400 #9C5C7C, 500 #7A4060, 600 #5C2E46, 700 #4A2539, 800 #3B1E2E, 900 #2C1622, 950 #1E0F17`.
- `gray` se redefine como neutro cálido (paleta *stone* de Tailwind): `50 #FAFAF9, 100 #F5F5F4, 200 #E7E5E4, 300 #D6D3D1, 400 #A8A29E, 500 #78716C, 600 #57534E, 700 #44403C, 800 #292524, 900 #1C1917, 950 #0C0A09`.
- `purple` se redefine como escala coral (el código usa `*-purple-*` para acentos): `50 #FDF4F1, 100 #FBE6DF, 200 #F6CBBD, 300 #EEA992, 400 #E0866A, 500 #D06A4C, 600 #B6553A, 700 #934430, 800 #74372A, 900 #5C2E25, 950 #33160F`.
- `rose` se redefine con la misma escala bordó que `blue` (const compartida `plum`), de modo que los botones rose del admin de Carta (p. ej. "Publicar") quedan en bordó.
- Nuevos `galia`: `cream #F5F1EA`, `plum #5C2E46`, `plum-dark #43203A`, `plum-light #8A5A72`, `lime #C5D94A`, `coral #E0866A`.
- `fontFamily`: `sans: ['"DM Sans"', 'system-ui', 'sans-serif']`, `display: ['Anton', 'Impact', 'sans-serif']`.

## 2. Variables shadcn (frontend/src/index.css, `:root`)
`--background` crema (`37 38% 94%`), `--foreground` bordó muy oscuro (`330 30% 14%`), `--primary` y `--ring` bordó (`329 33% 27%`), `--primary-foreground` crema, `--secondary/--muted/--accent` crema más oscuro (`37 30% 89%`), `--muted-foreground` (`25 8% 40%`), `--border/--input` (`35 20% 85%`). `.dark` no se toca.
Estilos base: `body` con `font-sans bg-background text-foreground`; `h1` con `font-display uppercase tracking-wide text-galia-plum` (sin cambiar tamaños existentes).

## 3. Fuentes y assets
- `frontend/index.html`: preconnect + Google Fonts `Anton` y `DM Sans:wght@400;500;700`.
- Copiar `menu-site/public/brand/{logo.png,flower-lime.png,flower-coral.png}` a `frontend/public/brand/`.

## 4. Marco
- **Sidebar** (`components/layout/Sidebar.jsx`): fondo `bg-galia-plum-dark`/`galia-plum`, texto crema; logo (`/brand/logo.png` en versión clara: aplicar `brightness-0 invert` o fondo crema redondeado detrás) arriba; ítem activo `bg-white/10` + ícono de flor lima (`/brand/flower-lime.png`, 14px); hover `bg-white/5`. Encabezados de grupo: Personal = coral, Finanzas = lima, Análisis = crema, Carta = rosa (`blue-200`), aplicados como color de texto/acento sobre el fondo oscuro (reemplaza `activeClass`/`headerClass` actuales).
- **Navbar** (`components/layout/Navbar.jsx`): fondo crema `bg-galia-cream`, borde inferior `border-gray-200`; "Galia" en `font-display` bordó.
- **Fondo de contenido** (`components/layout/Layout.jsx`): crema `bg-galia-cream` en lugar de `bg-gray-50`; las tarjetas permanecen blancas. Los `<h1>` de página no fijan color de texto y heredan el bordó global.
- **Login** (`pages/Login.jsx`): fondo crema, logo grande centrado, flores lima (arriba-izq) y coral (abajo-der) decorativas `aria-hidden`, botón bordó.

## 5. Verificación
Capturas en navegador (local) de Login, Dashboard, Empleados, Horarios, Ventas, Reportes, Sueldos, Carta: sin textos ilegibles ni restos azules/gris frío relevantes; `npm run build` OK.

## Fuera de alcance
Layout por pantalla, dark mode, cambios de comportamiento.
