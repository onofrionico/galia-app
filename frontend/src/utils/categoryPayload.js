// Cuerpo para crear o editar una categoría. Al editar, la estación solo se manda si el usuario la cambió:
// si la lista de estaciones no cargó, el select arranca vacío y no tiene que borrar la estación guardada.
export function categoryPayload(formData, original, { stationTouched = true } = {}) {
  const { station_id: station, ...rest } = formData
  if (original && !stationTouched) return rest
  return { ...rest, station_id: station === '' || station == null ? null : Number(station) }
}
