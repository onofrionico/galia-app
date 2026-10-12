// Sin conexión: aviso fijo arriba y una capa que bloquea los toques (ninguna acción sale sin red).
export default function ConnectivityBanner({ online }) {
  if (online) return null
  return (
    <>
      <div className="fixed inset-0 z-[55]" aria-hidden="true" />
      <div role="status"
        className="fixed inset-x-0 top-0 z-[60] bg-red-700 px-4 pb-2 pt-[calc(env(safe-area-inset-top)+0.5rem)] text-center text-sm font-medium text-white">
        Sin conexión — reintentando…
      </div>
    </>
  )
}
