import { useEffect, useState } from 'react'

export function useElementSize(ref) {
  const [size, setSize] = useState({ width: 0, height: 0 })
  useEffect(() => {
    const element = ref.current
    if (!element) return undefined
    const observer = new ResizeObserver(([entry]) =>
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height }))
    observer.observe(element)
    const rect = element.getBoundingClientRect()
    setSize({ width: rect.width, height: rect.height })
    return () => observer.disconnect()
  }, [ref])
  return size
}

export function useElementWidth(ref) {
  return useElementSize(ref).width
}
