import { useRef, useState } from 'react'
import { pinchZoom } from '../utils/zoom'

// Zoom con dos dedos sobre un contenedor (pointer events). El desplazamiento lo hace el scroll nativo:
// el contenedor debe tener touch-action: pan-x pan-y para que el navegador no haga su propio zoom.
export function usePinchZoom() {
  const [zoom, setZoom] = useState(1)
  const pointers = useRef(new Map())
  const start = useRef(null)

  const distance = () => {
    const [a, b] = [...pointers.current.values()]
    return Math.hypot(a.x - b.x, a.y - b.y)
  }

  const end = (event) => {
    pointers.current.delete(event.pointerId)
    if (pointers.current.size < 2) start.current = null
  }

  const handlers = {
    onPointerDown: (event) => {
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
      if (pointers.current.size === 2) start.current = { zoom, distance: distance() }
    },
    onPointerMove: (event) => {
      if (!pointers.current.has(event.pointerId)) return
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
      if (pointers.current.size === 2 && start.current) {
        setZoom(pinchZoom(start.current.zoom, start.current.distance, distance()))
      }
    },
    onPointerUp: end,
    onPointerCancel: end,
    onPointerLeave: end,
  }

  return { zoom, setZoom, handlers }
}
