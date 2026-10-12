export const MIN_ZOOM = 1
export const MAX_ZOOM = 3
export const ZOOM_STEP = 0.5

export const clampZoom = (zoom) =>
  Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Number.isFinite(zoom) ? zoom : MIN_ZOOM))

// Botones +/−: de a ZOOM_STEP, alineado al paso.
export const stepZoom = (zoom, direction) =>
  clampZoom(Math.round((zoom + direction * ZOOM_STEP) / ZOOM_STEP) * ZOOM_STEP)

// Pellizco: el zoom acompaña la proporción entre la distancia actual y la inicial de los dos dedos.
export const pinchZoom = (startZoom, startDistance, distance) =>
  clampZoom(startDistance > 0 ? (startZoom * distance) / startDistance : startZoom)
