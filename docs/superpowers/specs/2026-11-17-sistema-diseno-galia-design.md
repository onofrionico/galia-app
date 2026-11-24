# Aplicar el sistema de diseño de Galia a la app — Diseño

**Fecha:** 2026-11-17
**Estado:** Pendiente de aprobación
**Fuente de verdad:** artifact "Galia" (https://claude.ai/artifact/DVadrPwPoMSXDUZxmVWvbi): `project/README.md`, `tokens.json`, `components/bundle.css`, grupos de assets (Logos, Ilustraciones, Iconos, Stickers).

## Intención
El usuario ya definió el sistema de diseño de Galia. Quiere que la app (panel admin, POS, camarero, carta pública) lo use, para que todo se vea como la marca y no vuelva a divergir entre `frontend/` y `menu-site/`.

## Objetivos
- Paleta oficial en toda la app: ciruela `#673b4c`, terracota `#dd8c76`, lima `#cbd159`, crema `#edece4`, arena `#d1cdba` / `#e1ded0`, blanco.
- Tipografía oficial: Anton (títulos) + Poppins 300/400/500/700 (todo el texto). Reemplaza DM Sans.
- Una sola definición de tokens compartida por `frontend/` y `menu-site/`.
- Capa de marca visible: logo oficial, ilustraciones, pastilla de precio, etiqueta, cartel de título, divisor punteado.
- Regla de contraste del sistema: terracota y lima nunca como texto sobre crema.

## No objetivos
- Rediseñar el layout o el comportamiento de ninguna pantalla.
- Modo oscuro.
- Cargar Git Sans (el wordmark queda dentro de las imágenes del logo).
- Rehacer el sistema de diseño en sí.

## Anti-objetivos (fallaría aunque "funcione")
- Que el POS táctil pierda legibilidad o tamaño de botones.
- Texto ilegible: coral o lima sobre crema, o blanco sobre terracota (2.5:1).
- Cargar ilustraciones pesadas (algunas SVG pesan hasta 634 KB) en pantallas frecuentes.

## Restricciones
- Ramas desde `origin/main` actualizado; mergear la base antes de abrir cada PR.
- Valores de marca en config, no hardcodeados por pantalla (regla de trabajo del usuario).
- Verificar levantando la app y mirando pantallas reales, no solo `npm run build`.
- Las migraciones existentes no se tocan; no se prevén migraciones nuevas.

## Enfoques considerados
- **A. Solo tokens:** seguro y global, pero sin ilustraciones ni componentes.
- **B. Tokens + capa de marca:** elegido por el usuario.
- **C. Pasada pantalla por pantalla:** fiel pero grande, y arriesga el POS táctil.

## Diseño (B)

### PR 1 — Tokens y tipografía
1. **Preset compartido** `shared/galia-tailwind-preset.js` (o equivalente que ambos proyectos puedan importar; el builder elige el mecanismo) con: colores `galia.*`, escalas `plum`/`terracotta`/`lime`, fuentes `display: Anton` y `sans: Poppins`, radios `galia-lg 24px`, `galia-sm 6px`, `pill`. `frontend/tailwind.config.js` y `menu-site/tailwind.config.js` lo extienden.
2. **Escalas remapeadas (`blue`, `rose`, `purple`, `gray`)**: se mantienen los remapeos actuales para no tocar ~58 archivos, pero re-ancladas a la paleta oficial: la escala plum pasa a tener `700 = #673b4c`; la escala terracota se re-ancla a `#dd8c76`. *(Decisión mía: la escala exacta la deriva el builder y la deja documentada junto al preset.)*
3. **`frontend/src/index.css`**: variables shadcn (`--background`, `--primary`, `--ring`, etc.) recalculadas desde la paleta oficial; `body` en Poppins; `h1` en Anton.
4. **Fuentes**: `frontend/index.html`, `menu-site/index.html`, `links.html`, `cafecitos.html` cargan `Anton` y `Poppins:300;400;500;700` (hoy DM Sans). Las impresiones/PDF del backend no se tocan.
5. **Paleta vieja**: `frontend/src/constants/colors.js` pasa a leer los valores oficiales; `PosTopBar` deja de usar `#D4E157`/`#6B4C5C`/`#E8DCC4`.
6. **Valores sueltos**: color por defecto de tags de carta (`#5C2E46` en `backend/app/models/menu.py`, `routes/menu.py`, `MenuSettingsPanel.jsx`) y color del QR en `CafecitosApp.jsx` pasan a los valores oficiales. Los tags ya guardados en la base no se migran (no se pierde nada; solo cambia el default de los nuevos).
7. **Auditoría de contraste**: ~35 usos de `text-purple-*` (coral como texto) y 2 de `text-galia-coral/lime`: se cambian a ciruela, o el elemento pasa a fondo terracota con texto ciruela a 24px o más.

### PR 2 — Capa de marca
1. **Clases `galia-*`** del sistema (`galia-price`, `galia-label`, `galia-banner`, `galia-sticker`, `galia-divider`, `galia-card`) como componentes de Tailwind (`@layer components`) en el preset, con los mismos nombres y valores que `bundle.css`.
2. **Carta pública (`menu-site`)**: precios en pastilla, etiquetas de categoría en pastilla ciruela, títulos de sección con `galia-banner`, divisores punteados terracota, tarjetas `galia-card` (radio 24).
3. **Login y estados vacíos del panel**: logo oficial y 1 ilustración por pantalla (cafetera con flores, tazas apiladas, torta). Se descargan del sistema y se copian como SVG optimizados a `frontend/public/brand/` y `menu-site/public/brand/`; sin cargar las >300 KB en pantallas frecuentes.
4. **Sidebar y navbar**: logo oficial (versión crema sobre ciruela) en lugar del PNG actual; flor lima del sistema para el ítem activo.
5. **Logos oficiales**: se reemplazan los logos actuales por los de Drive (*Formales/Logos fondo Transp*), que están en la paleta correcta; los del artifact usan la ciruela magenta vieja y no se usan. Si no se puede acceder a Drive, se avisa y se pide el archivo, no se aproxima.
6. **Favicons y manifest**: regenerados desde el símbolo oficial.

### Alcance de forma (mi decisión, el usuario no la fijó)
- **Radio 24px y pastillas** en: carta pública, login, tarjetas destacadas del Dashboard y componentes `galia-*`.
- **Panel admin denso, POS y camarero** mantienen sus radios actuales (8–12px) para no perder densidad ni tamaño táctil. Reversible: está todo en el preset.

## Verificación
- `npm run build` de `frontend/` y `menu-site/`.
- Levantar ambos proyectos y revisar con capturas: Login, Dashboard, Empleados, Horarios, Ventas, Productos, Recetas, Carta (admin), POS caja, mostrador y camarero, y la carta pública y `/cafecitos`.
- Chequeo de contraste (≥4.5:1 texto) en los pares usados.
- Sin textos en coral/lima sobre crema (búsqueda en el código).
- Los tests existentes siguen pasando (`menu-site` tiene tests de `categoryFlower`).

## Lo que queda al builder
- Mecanismo exacto para compartir el preset entre `frontend/` y `menu-site/` (carpeta hermana vs. paquete local).
- Valores intermedios de las escalas 50–950.
- Qué ilustración va en cada estado vacío, y el orden de los assets más livianos.
- Optimización de SVG (por ejemplo `svgo`).
