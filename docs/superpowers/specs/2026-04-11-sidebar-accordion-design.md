# Sidebar Accordion — Diseño

**Fecha:** 2026-04-11  
**Estado:** Aprobado

## Contexto

El sidebar actual del panel admin lista 15+ ítems planos sin jerarquía visual, generando sobrecarga cognitiva. Los ítems relacionados no están agrupados (ej: "Categorías de Gastos" separada de "Gastos"). Algunos ítems son sub-tareas de otros pero aparecen al mismo nivel.

**Audiencia por rol:**
- **Admin:** usa principalmente desktop
- **Empleado:** usa principalmente mobile — su sidebar queda sin cambios (solo 6 ítems, drawer actual funciona bien)

## Decisiones de Diseño

| Pregunta | Decisión |
|---|---|
| Mecanismo de agrupación | Accordion colapsable (grupos que se abren/cierran) |
| Comportamiento | Solo un grupo abierto a la vez (accordion exclusivo) |
| Scope del cambio | Solo sidebar admin; sidebar empleado sin cambios |

## Estructura del Sidebar Admin

### Ítems siempre visibles (fuera de grupos)
- `Dashboard` — `/dashboard`
- `Mi Perfil` — `/profile`

### Grupo: Personal
Ícono: `Users` | Color de acento: verde (`#16a34a`, `#f0fdf4`, `#bbf7d0`)

| Ítem | Ruta | Nivel |
|---|---|---|
| Horarios | `/schedules` | principal |
| Gestión de Horas | `/admin-time-tracking` | principal |
| Importar Horas | `/import-time-tracking` | sub-ítem (indentado) |
| Solicitudes de Ausencia | `/absence-requests` | principal |
| Empleados | `/employees` | principal |
| Puestos | `/job-positions` | principal |
| Feriados | `/holidays` | principal |

### Grupo: Finanzas
Ícono: `DollarSign` (o similar) | Color de acento: azul (`#1d4ed8`, `#eff6ff`, `#bfdbfe`)

| Ítem | Ruta | Nivel |
|---|---|---|
| Ventas | `/sales` | principal |
| Gastos | `/expenses` | principal |
| Categorías de Gastos | `/expense-categories` | sub-ítem (indentado) |
| Sueldos | `/payroll` | principal |
| Reclamos de Nóminas | `/payroll-claims` | sub-ítem (indentado) |

### Grupo: Análisis
Ícono: `BarChart3` | Color de acento: violeta (`#7c3aed`, `#faf5ff`, `#e9d5ff`)

| Ítem | Ruta | Nivel |
|---|---|---|
| Reportes | `/reports` | principal |
| Dashboard ML | `/ml-dashboard` | principal |

## Comportamiento

### Accordion exclusivo
- Solo un grupo puede estar abierto a la vez.
- Al hacer click en un grupo cerrado, el grupo abierto se cierra primero (con animación suave), luego el nuevo se abre.
- Al hacer click en el grupo ya abierto, se cierra.

### Auto-apertura por ruta activa
- Al montar el componente (y en cada cambio de ruta), se determina qué grupo contiene la ruta activa.
- Ese grupo se abre automáticamente.
- El ítem activo recibe el estilo `bg-primary text-primary-foreground` (comportamiento actual preservado).

### Persistencia de estado
- El nombre del grupo abierto se guarda en `localStorage` bajo la clave `sidebar_open_group`.
- Al montar, si hay un grupo guardado Y la ruta activa no pertenece a otro grupo, se restaura el guardado.
- La ruta activa tiene prioridad sobre `localStorage`.

### Sub-ítems
- Se renderizan indentados (`pl-6` o similar) con tamaño de fuente menor (`text-xs` o `text-sm`).
- Incluyen un prefijo visual `↳` para indicar la jerarquía.
- Participan del resaltado de ítem activo igual que los ítems principales.

## Cambios de Código

### Archivo a modificar
`frontend/src/components/layout/Sidebar.jsx`

### Estructura de datos nueva
El array `navItems` se reemplaza por una estructura `navGroups` con grupos y sub-ítems:

```js
const navGroups = [
  {
    id: 'personal',
    label: 'Personal',
    icon: Users,
    color: { text: 'text-green-700', bg: 'bg-green-50', border: 'border-green-200' },
    items: [
      { to: '/schedules', icon: Calendar, label: 'Horarios' },
      { to: '/admin-time-tracking', icon: Clock, label: 'Gestión de Horas' },
      { to: '/import-time-tracking', icon: Upload, label: 'Importar Horas', subItem: true },
      { to: '/absence-requests', icon: FileText, label: 'Solicitudes de Ausencia' },
      { to: '/employees', icon: Users, label: 'Empleados' },
      { to: '/job-positions', icon: Briefcase, label: 'Puestos' },
      { to: '/holidays', icon: CalendarDays, label: 'Feriados' },
    ]
  },
  {
    id: 'finanzas',
    label: 'Finanzas',
    icon: DollarSign,
    color: { text: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-200' },
    items: [
      { to: '/sales', icon: ShoppingCart, label: 'Ventas' },
      { to: '/expenses', icon: Receipt, label: 'Gastos' },
      { to: '/expense-categories', icon: Tag, label: 'Categorías de Gastos', subItem: true },
      { to: '/payroll', icon: Wallet, label: 'Sueldos' },
      { to: '/payroll-claims', icon: AlertTriangle, label: 'Reclamos de Nóminas', subItem: true },
    ]
  },
  {
    id: 'analisis',
    label: 'Análisis',
    icon: BarChart3,
    color: { text: 'text-purple-700', bg: 'bg-purple-50', border: 'border-purple-200' },
    items: [
      { to: '/reports', icon: BarChart3, label: 'Reportes' },
      { to: '/ml-dashboard', icon: Brain, label: 'Dashboard ML' },
    ]
  }
]
```

### Lógica de estado
```js
const location = useLocation()

// Determinar qué grupo contiene la ruta activa
const activeGroup = navGroups.find(g => g.items.some(i => location.pathname.startsWith(i.to)))?.id ?? null

// Estado del grupo abierto (ruta activa tiene prioridad)
const [openGroup, setOpenGroup] = useState(() => {
  return activeGroup ?? localStorage.getItem('sidebar_open_group') ?? null
})

// Sincronizar cuando cambia la ruta
useEffect(() => {
  if (activeGroup) {
    setOpenGroup(activeGroup)
    localStorage.setItem('sidebar_open_group', activeGroup)
  }
}, [location.pathname])

function handleGroupClick(groupId) {
  const next = openGroup === groupId ? null : groupId
  setOpenGroup(next)
  if (next) localStorage.setItem('sidebar_open_group', next)
}
```

## Lo que NO cambia
- Sidebar de **empleados**: sin modificaciones, el drawer mobile actual es correcto.
- Estilos de ítem activo (`bg-primary text-primary-foreground`).
- Comportamiento de cierre en mobile (`onClose` al navegar).
- Overlay mobile al abrir el sidebar.
- Estructura de `Layout.jsx` y `Navbar.jsx`.

## Criterios de Aceptación
- [ ] Los 3 grupos se muestran con su ícono y label en el sidebar admin.
- [ ] Solo un grupo puede estar abierto a la vez.
- [ ] Al navegar a cualquier ruta, el grupo correspondiente se abre automáticamente.
- [ ] Los sub-ítems se muestran indentados y con fuente menor.
- [ ] El ítem activo mantiene el estilo resaltado actual.
- [ ] El estado del grupo abierto persiste en `localStorage`.
- [ ] El sidebar de empleados no tiene cambios visibles.
- [ ] La transición de apertura/cierre tiene animación suave.
