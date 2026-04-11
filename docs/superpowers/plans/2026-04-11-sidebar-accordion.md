# Sidebar Accordion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el sidebar plano del admin con un accordion de 3 grupos (Personal, Finanzas, Análisis) que solo permite un grupo abierto a la vez y se auto-abre según la ruta activa.

**Architecture:** Modificación de un único componente React (`Sidebar.jsx`). Se reemplaza el array plano `navItems` por una estructura `navGroups` con grupos y sub-ítems. El estado del grupo abierto se maneja con `useState` + `useEffect` (sincronizado con `useLocation`), con persistencia en `localStorage`. El sidebar de empleados (no-admin) no cambia.

**Tech Stack:** React 18, React Router v6 (`useLocation`), Tailwind CSS v3, Lucide React icons.

---

## File Map

| Acción | Archivo | Qué hace |
|---|---|---|
| Modify | `frontend/src/components/layout/Sidebar.jsx` | Único archivo a tocar — todo el cambio va acá |

---

## Task 1: Actualizar imports y definir la estructura `navGroups`

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.jsx`

- [ ] **Step 1: Abrir el archivo actual**

Leer `frontend/src/components/layout/Sidebar.jsx`. El archivo actual importa íconos de lucide-react y define `navItems` como un array plano. Lo vamos a reemplazar completamente.

- [ ] **Step 2: Reemplazar el contenido del archivo con la nueva estructura**

El archivo completo queda así — primero los imports y `navGroups`, la lógica la agregamos en Task 2:

```jsx
import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { ChevronDown, X, LayoutDashboard, User } from 'lucide-react'
import {
  Calendar,
  Clock,
  Upload,
  FileText,
  Users,
  Briefcase,
  CalendarDays,
  ShoppingCart,
  Receipt,
  Tag,
  Wallet,
  AlertTriangle,
  BarChart3,
  Brain,
  DollarSign,
  LogIn,
} from 'lucide-react'

// Ítems siempre visibles (fuera de grupos) para admin y empleado
const alwaysVisibleAdmin = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/profile', icon: User, label: 'Mi Perfil' },
]

const alwaysVisibleEmployee = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/my-schedule', icon: Clock, label: 'Mi Horario' },
  { to: '/time-tracking', icon: LogIn, label: 'Carga de Horarios' },
  { to: '/my-payrolls', icon: Wallet, label: 'Mis Nóminas' },
  { to: '/my-documents', icon: FileText, label: 'Mis Recibos' },
  { to: '/my-absence-requests', icon: FileText, label: 'Mis Ausencias' },
  { to: '/profile', icon: User, label: 'Mi Perfil' },
]

// Grupos accordion — solo para admin
const navGroups = [
  {
    id: 'personal',
    label: 'Personal',
    icon: Users,
    activeClass: 'text-green-700 bg-green-50 border-green-200',
    headerClass: 'text-green-700 bg-green-50',
    items: [
      { to: '/schedules', icon: Calendar, label: 'Horarios' },
      { to: '/admin-time-tracking', icon: Clock, label: 'Gestión de Horas' },
      { to: '/import-time-tracking', icon: Upload, label: 'Importar Horas', subItem: true },
      { to: '/absence-requests', icon: FileText, label: 'Solicitudes de Ausencia' },
      { to: '/employees', icon: Users, label: 'Empleados' },
      { to: '/job-positions', icon: Briefcase, label: 'Puestos' },
      { to: '/holidays', icon: CalendarDays, label: 'Feriados' },
    ],
  },
  {
    id: 'finanzas',
    label: 'Finanzas',
    icon: DollarSign,
    activeClass: 'text-blue-700 bg-blue-50 border-blue-200',
    headerClass: 'text-blue-700 bg-blue-50',
    items: [
      { to: '/sales', icon: ShoppingCart, label: 'Ventas' },
      { to: '/expenses', icon: Receipt, label: 'Gastos' },
      { to: '/expense-categories', icon: Tag, label: 'Categorías de Gastos', subItem: true },
      { to: '/payroll', icon: Wallet, label: 'Sueldos' },
      { to: '/payroll-claims', icon: AlertTriangle, label: 'Reclamos de Nóminas', subItem: true },
    ],
  },
  {
    id: 'analisis',
    label: 'Análisis',
    icon: BarChart3,
    activeClass: 'text-purple-700 bg-purple-50 border-purple-200',
    headerClass: 'text-purple-700 bg-purple-50',
    items: [
      { to: '/reports', icon: BarChart3, label: 'Reportes' },
      { to: '/ml-dashboard', icon: Brain, label: 'Dashboard ML' },
    ],
  },
]
```

- [ ] **Step 3: Verificar que no hay errores de lint**

```bash
cd frontend && npm run lint -- --max-warnings 0 2>&1 | head -30
```

Esperado: sin errores nuevos (puede haber warnings de variables no usadas aún — es normal, los resolvemos en Task 2).

---

## Task 2: Agregar lógica de estado del accordion

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.jsx`

- [ ] **Step 1: Reemplazar el componente `Sidebar` con la lógica de estado**

```jsx
const Sidebar = ({ isOpen, onClose }) => {
  const { isAdmin } = useAuth()
  const location = useLocation()

  // Encontrar qué grupo contiene la ruta activa
  const getActiveGroup = (pathname) =>
    navGroups.find(g => g.items.some(i => pathname.startsWith(i.to)))?.id ?? null

  const [openGroup, setOpenGroup] = useState(() => {
    const fromRoute = getActiveGroup(location.pathname)
    if (fromRoute) return fromRoute
    return localStorage.getItem('sidebar_open_group') ?? null
  })

  // Sincronizar cuando cambia la ruta
  useEffect(() => {
    const fromRoute = getActiveGroup(location.pathname)
    if (fromRoute) {
      setOpenGroup(fromRoute)
      localStorage.setItem('sidebar_open_group', fromRoute)
    }
  }, [location.pathname])

  const handleGroupClick = (groupId) => {
    const next = openGroup === groupId ? null : groupId
    setOpenGroup(next)
    if (next) {
      localStorage.setItem('sidebar_open_group', next)
    } else {
      localStorage.removeItem('sidebar_open_group')
    }
  }

  // ... JSX en Task 3
}
```

- [ ] **Step 2: Confirmar que `useLocation` funciona dentro del Router**

`Sidebar` se renderiza dentro de `Layout`, que está dentro del `<Router>` en `App.jsx`. `useLocation` está disponible — no se necesita ningún cambio en archivos padres.

---

## Task 3: Implementar el JSX del sidebar

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.jsx`

- [ ] **Step 1: Agregar el JSX completo al componente**

Completar el `return` del componente `Sidebar`. El archivo completo final es:

```jsx
import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { ChevronDown, X, LayoutDashboard, User } from 'lucide-react'
import {
  Calendar,
  Clock,
  Upload,
  FileText,
  Users,
  Briefcase,
  CalendarDays,
  ShoppingCart,
  Receipt,
  Tag,
  Wallet,
  AlertTriangle,
  BarChart3,
  Brain,
  DollarSign,
  LogIn,
} from 'lucide-react'

const alwaysVisibleAdmin = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/profile', icon: User, label: 'Mi Perfil' },
]

const alwaysVisibleEmployee = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/my-schedule', icon: Clock, label: 'Mi Horario' },
  { to: '/time-tracking', icon: LogIn, label: 'Carga de Horarios' },
  { to: '/my-payrolls', icon: Wallet, label: 'Mis Nóminas' },
  { to: '/my-documents', icon: FileText, label: 'Mis Recibos' },
  { to: '/my-absence-requests', icon: FileText, label: 'Mis Ausencias' },
  { to: '/profile', icon: User, label: 'Mi Perfil' },
]

const navGroups = [
  {
    id: 'personal',
    label: 'Personal',
    icon: Users,
    activeClass: 'text-green-700 bg-green-50 border-green-200',
    headerClass: 'text-green-700 bg-green-50',
    items: [
      { to: '/schedules', icon: Calendar, label: 'Horarios' },
      { to: '/admin-time-tracking', icon: Clock, label: 'Gestión de Horas' },
      { to: '/import-time-tracking', icon: Upload, label: 'Importar Horas', subItem: true },
      { to: '/absence-requests', icon: FileText, label: 'Solicitudes de Ausencia' },
      { to: '/employees', icon: Users, label: 'Empleados' },
      { to: '/job-positions', icon: Briefcase, label: 'Puestos' },
      { to: '/holidays', icon: CalendarDays, label: 'Feriados' },
    ],
  },
  {
    id: 'finanzas',
    label: 'Finanzas',
    icon: DollarSign,
    activeClass: 'text-blue-700 bg-blue-50 border-blue-200',
    headerClass: 'text-blue-700 bg-blue-50',
    items: [
      { to: '/sales', icon: ShoppingCart, label: 'Ventas' },
      { to: '/expenses', icon: Receipt, label: 'Gastos' },
      { to: '/expense-categories', icon: Tag, label: 'Categorías de Gastos', subItem: true },
      { to: '/payroll', icon: Wallet, label: 'Sueldos' },
      { to: '/payroll-claims', icon: AlertTriangle, label: 'Reclamos de Nóminas', subItem: true },
    ],
  },
  {
    id: 'analisis',
    label: 'Análisis',
    icon: BarChart3,
    activeClass: 'text-purple-700 bg-purple-50 border-purple-200',
    headerClass: 'text-purple-700 bg-purple-50',
    items: [
      { to: '/reports', icon: BarChart3, label: 'Reportes' },
      { to: '/ml-dashboard', icon: Brain, label: 'Dashboard ML' },
    ],
  },
]

const Sidebar = ({ isOpen, onClose }) => {
  const { isAdmin } = useAuth()
  const location = useLocation()

  const getActiveGroup = (pathname) =>
    navGroups.find(g => g.items.some(i => pathname.startsWith(i.to)))?.id ?? null

  const [openGroup, setOpenGroup] = useState(() => {
    const fromRoute = getActiveGroup(location.pathname)
    if (fromRoute) return fromRoute
    return localStorage.getItem('sidebar_open_group') ?? null
  })

  useEffect(() => {
    const fromRoute = getActiveGroup(location.pathname)
    if (fromRoute) {
      setOpenGroup(fromRoute)
      localStorage.setItem('sidebar_open_group', fromRoute)
    }
  }, [location.pathname])

  const handleGroupClick = (groupId) => {
    const next = openGroup === groupId ? null : groupId
    setOpenGroup(next)
    if (next) {
      localStorage.setItem('sidebar_open_group', next)
    } else {
      localStorage.removeItem('sidebar_open_group')
    }
  }

  // Helper: render a single nav link (used for always-visible items and group items)
  const renderNavLink = (item, extraClass = '') => {
    const Icon = item.icon
    return (
      <NavLink
        key={item.to}
        to={item.to}
        onClick={onClose}
        className={({ isActive }) =>
          `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
            isActive
              ? 'bg-primary text-primary-foreground'
              : 'text-gray-700 hover:bg-gray-100'
          } ${extraClass}`
        }
      >
        <Icon className="h-4 w-4 flex-shrink-0" />
        <span className="font-medium">{item.label}</span>
      </NavLink>
    )
  }

  return (
    <>
      <aside className={`fixed md:static top-0 left-0 z-40 w-64 bg-white border-r min-h-screen transition-transform duration-300 transform ${
        isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      }`}>
        <nav className="p-4 space-y-1 md:mt-0 mt-16">
          <button
            onClick={onClose}
            className="md:hidden absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-6 w-6 text-gray-600" />
          </button>

          {/* Admin: siempre visibles + grupos accordion */}
          {isAdmin() ? (
            <>
              {alwaysVisibleAdmin.map(item => renderNavLink(item))}

              <div className="pt-2 space-y-1">
                {navGroups.map(group => {
                  const GroupIcon = group.icon
                  const isOpen = openGroup === group.id
                  const isGroupActive = getActiveGroup(location.pathname) === group.id

                  return (
                    <div
                      key={group.id}
                      className={`rounded-lg border overflow-hidden transition-colors ${
                        isGroupActive ? group.activeClass : 'border-gray-200'
                      }`}
                    >
                      {/* Group header button */}
                      <button
                        onClick={() => handleGroupClick(group.id)}
                        className={`w-full flex items-center justify-between px-4 py-2.5 text-sm font-semibold transition-colors ${
                          isGroupActive ? group.headerClass : 'text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        <span className="flex items-center gap-3">
                          <GroupIcon className="h-4 w-4 flex-shrink-0" />
                          {group.label}
                        </span>
                        <ChevronDown
                          className={`h-4 w-4 transition-transform duration-200 ${
                            isOpen ? 'rotate-180' : ''
                          }`}
                        />
                      </button>

                      {/* Group items */}
                      <div
                        className={`overflow-hidden transition-all duration-200 ease-in-out ${
                          isOpen ? 'max-h-96' : 'max-h-0'
                        }`}
                      >
                        <div className="pb-2 pt-1 px-2 space-y-0.5">
                          {group.items.map(item => {
                            const Icon = item.icon
                            return (
                              <NavLink
                                key={item.to}
                                to={item.to}
                                onClick={onClose}
                                className={({ isActive }) =>
                                  `flex items-center gap-3 rounded-md transition-colors ${
                                    item.subItem
                                      ? 'pl-7 pr-3 py-2 text-xs'
                                      : 'px-3 py-2 text-sm'
                                  } ${
                                    isActive
                                      ? 'bg-primary text-primary-foreground font-medium'
                                      : 'text-gray-600 hover:bg-gray-100'
                                  }`
                                }
                              >
                                <Icon className="h-3.5 w-3.5 flex-shrink-0" />
                                <span className={item.subItem ? '' : 'font-medium'}>
                                  {item.label}
                                </span>
                              </NavLink>
                            )
                          })}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          ) : (
            /* Empleado: lista plana sin cambios */
            alwaysVisibleEmployee.map(item => renderNavLink(item))
          )}
        </nav>
      </aside>

      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={onClose}
        />
      )}
    </>
  )
}

export default Sidebar
```

- [ ] **Step 2: Verificar que no hay errores de lint**

```bash
cd frontend && npm run lint 2>&1 | head -40
```

Esperado: sin errores. Si hay warnings de `exhaustive-deps` por `getActiveGroup` dentro del `useEffect`, es seguro ignorarlos (la función no cambia entre renders) o moverla afuera del componente.

---

## Task 4: Verificación manual en el browser

**Files:** ninguno nuevo — solo verificación

- [ ] **Step 1: Levantar el servidor de desarrollo**

```bash
cd frontend && npm run dev
```

Navegar a `http://localhost:5173` e iniciar sesión como **admin**.

- [ ] **Step 2: Verificar comportamiento del accordion**

Checklist:
- [ ] Se muestran Dashboard y Mi Perfil siempre visibles arriba
- [ ] Se muestran 3 grupos: Personal, Finanzas, Análisis
- [ ] Al hacer click en un grupo, se abre con animación suave
- [ ] Al abrir otro grupo, el anterior se cierra automáticamente
- [ ] El `ChevronDown` rota 180° cuando el grupo está abierto
- [ ] El grupo activo (con la página actual) tiene color de acento diferente al borde/header
- [ ] Los sub-ítems (Importar Horas, Categorías de Gastos, Reclamos de Nóminas) aparecen indentados y con texto más pequeño

- [ ] **Step 3: Verificar auto-apertura por ruta activa**

- Navegar directamente a `/sales` — el grupo "Finanzas" debe estar abierto
- Navegar a `/employees` — el grupo "Personal" debe estar abierto
- Navegar a `/reports` — el grupo "Análisis" debe estar abierto

- [ ] **Step 4: Verificar persistencia en localStorage**

- Abrir "Finanzas", luego refrescar la página (F5)
- El grupo "Finanzas" debe seguir abierto (restaurado desde `localStorage`)
- Navegar a `/schedules` — "Personal" debe abrirse (ruta activa tiene prioridad)

- [ ] **Step 5: Verificar sidebar de empleados**

Cerrar sesión e iniciar sesión como **empleado**. Verificar:
- [ ] El sidebar muestra la lista plana original (sin grupos ni accordion)
- [ ] Los 6 ítems aparecen exactamente igual que antes

- [ ] **Step 6: Verificar mobile (admin)**

En DevTools, activar viewport mobile (375px).
- [ ] El sidebar se abre/cierra con el botón hamburguesa
- [ ] El accordion funciona igual dentro del drawer mobile
- [ ] Al hacer click en un ítem, el drawer se cierra (`onClose` se llama)

---

## Task 5: Commit final

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.jsx`

- [ ] **Step 1: Revisar el diff antes de commitear**

```bash
cd frontend && git diff src/components/layout/Sidebar.jsx
```

Confirmar que solo cambió `Sidebar.jsx` y que el diff se ve limpio.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/layout/Sidebar.jsx
git commit -m "$(cat <<'EOF'
feat: reorganize admin sidebar into collapsible accordion groups

Groups admin nav items into Personal, Finanzas, and Análisis sections
with exclusive accordion behavior. Active route auto-opens its group.
State persists in localStorage. Employee sidebar unchanged.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Spec Coverage Check

| Requisito del spec | Tarea que lo implementa |
|---|---|
| Grupos: Personal, Finanzas, Análisis | Task 1 — `navGroups` |
| Solo un grupo abierto a la vez | Task 2 — `handleGroupClick` cierra el anterior |
| Auto-apertura por ruta activa | Task 2 — `useEffect` + `getActiveGroup` |
| Sub-ítems indentados (Importar Horas, Categorías, Reclamos) | Task 3 — flag `subItem: true` + clases `pl-7 text-xs` |
| Persistencia en localStorage | Task 2 — `localStorage.setItem/removeItem` |
| Ítem activo resaltado (`bg-primary`) | Task 3 — `NavLink` con `isActive` |
| Dashboard y Mi Perfil siempre visibles | Task 3 — `alwaysVisibleAdmin` fuera de grupos |
| Sidebar empleados sin cambios | Task 3 — rama `else` en el JSX |
| Animación suave | Task 3 — `transition-all duration-200` + `max-h-0/max-h-96` |
