const FAILURES_TO_OFFLINE = 2

export const initialConnectivity = { online: true, failures: 0 }

// Estado de conexión del celular a partir de los eventos del navegador y del polling a /changes.
// Solo una consulta exitosa reconecta: el evento 'online' del navegador no garantiza llegar al servidor.
export function connectivityReducer(state, event) {
  switch (event) {
    case 'offline':
      return { ...state, online: false }
    case 'poll-ok':
      return { online: true, failures: 0 }
    case 'poll-http-error':
      return { ...state, failures: 0 }
    case 'poll-network-error': {
      const failures = state.failures + 1
      return { online: state.online && failures < FAILURES_TO_OFFLINE, failures }
    }
    default:
      return state
  }
}

// Un error con respuesta HTTP (4xx/5xx) significa que el servidor respondió: no es falta de red.
export const pollEvent = (ok, error) => {
  if (ok) return 'poll-ok'
  return error?.response ? 'poll-http-error' : 'poll-network-error'
}
