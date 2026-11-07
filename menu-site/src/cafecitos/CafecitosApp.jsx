import { useCallback, useEffect, useRef, useState } from 'react'
import QRCode from 'qrcode'
import { ApiError, cafecitosApi } from './api'
import { reachable } from './labels'
import { clearToken, getToken, setToken } from './session'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
const GSI_SRC = 'https://accounts.google.com/gsi/client'

function loadGoogle() {
  if (window.google?.accounts?.id) return Promise.resolve(window.google)
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = GSI_SRC
    script.async = true
    script.onload = () => resolve(window.google)
    script.onerror = () => reject(new Error('No se pudo cargar Google'))
    document.head.appendChild(script)
  })
}

function GoogleButton({ onCredential }) {
  const ref = useRef(null)
  const [error, setError] = useState('')
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      setError('El ingreso con Google todavía no está configurado.')
      return
    }
    loadGoogle().then((google) => {
      google.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: (r) => onCredential(r.credential) })
      google.accounts.id.renderButton(ref.current, { theme: 'outline', size: 'large', text: 'signin_with', locale: 'es' })
    }).catch(() => setError('No se pudo cargar el ingreso con Google.'))
  }, [onCredential])
  return (
    <div className="flex flex-col items-center gap-2">
      <div ref={ref} aria-label="Entrar con Google" />
      {error && <p className="text-sm text-coral">{error}</p>}
    </div>
  )
}

function Welcome({ onLoggedIn }) {
  const [pending, setPending] = useState(null) // { credential, firstName } cuando falta aceptar términos
  const [terms, setTerms] = useState(false)
  const [promo, setPromo] = useState(false)
  const [error, setError] = useState('')

  const login = useCallback(async (credential, extra) => {
    setError('')
    try {
      const { token } = await cafecitosApi.loginWithGoogle(credential, extra)
      setToken(token)
      onLoggedIn()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409 && err.body?.needs_terms) {
        setPending({ credential, firstName: err.body.first_name })
      } else {
        setError(err.message)
      }
    }
  }, [onLoggedIn])

  return (
    <section className="mt-6 rounded-3xl bg-white/70 p-6 text-center shadow-sm">
      <h2 className="font-display text-3xl uppercase text-plum">Mis cafecitos</h2>
      <p className="mt-2 text-plum-light">
        Cada compra en Galia suma cafecitos. Juntalos y canjealos por premios en la caja.
      </p>
      {!pending && (
        <div className="mt-5">
          <p className="mb-3 font-medium text-plum">Entrar con Google</p>
          <GoogleButton onCredential={(credential) => login(credential)} />
        </div>
      )}
      {pending && (
        <form className="mt-5 space-y-3 text-left" onSubmit={(e) => { e.preventDefault(); login(pending.credential, { accept_terms: true, promo_opt_in: promo }) }}>
          <p className="font-medium text-plum">¡Hola{pending.firstName ? `, ${pending.firstName}` : ''}! Un paso más:</p>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} className="mt-1" required />
            <span>Acepto los términos del programa de cafecitos y que Galia guarde mis datos para usarlo.</span>
          </label>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={promo} onChange={(e) => setPromo(e.target.checked)} className="mt-1" />
            <span>Quiero recibir promociones por mail (opcional).</span>
          </label>
          <button type="submit" disabled={!terms} className="w-full rounded-full bg-plum py-3 font-bold text-cream disabled:opacity-40">
            Crear mi cuenta
          </button>
        </form>
      )}
      {error && <p className="mt-3 text-sm text-coral">{error}</p>}
    </section>
  )
}

function Wallet({ onLogout }) {
  const [state, setState] = useState({ status: 'loading' })
  const [qr, setQr] = useState('')
  const [phone, setPhone] = useState('')
  const [saved, setSaved] = useState('')

  const load = useCallback(async () => {
    try {
      const [me, movements, rewards] = await Promise.all([cafecitosApi.me(), cafecitosApi.movements(), cafecitosApi.rewards()])
      setState({ status: 'ready', me, movements, rewards })
      setPhone(me.phone || '')
      setQr(await QRCode.toDataURL(me.qr_token, { margin: 1, width: 240, color: { dark: '#43203A', light: '#FFFFFF' } }))
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onLogout()
      else setState({ status: 'error', message: err.message })
    }
  }, [onLogout])

  useEffect(() => { load() }, [load])

  if (state.status === 'loading') return <p className="mt-10 text-center text-plum-light">Cargando…</p>
  if (state.status === 'error') return <p className="mt-10 text-center text-coral">{state.message}</p>
  const { me, movements, rewards } = state
  const { available, next } = reachable(me.balance, rewards)

  const savePhone = async (e) => {
    e.preventDefault()
    await cafecitosApi.updateMe({ phone })
    setSaved('Guardado')
  }

  return (
    <div className="mt-6 space-y-5">
      <section className="rounded-3xl bg-white/80 p-6 text-center shadow-sm">
        <p className="text-plum-light">Hola, {me.first_name || 'cliente'}</p>
        <p className="font-display text-6xl text-plum">{me.balance} <span aria-hidden="true">☕</span></p>
        <p className="text-plum-light">cafecitos</p>
        {qr && <img src={qr} alt="Tu código QR para la caja" className="mx-auto mt-4 h-56 w-56 rounded-xl" />}
        <p className="mt-2 text-sm text-plum-light">Mostralo en la caja</p>
      </section>

      <section className="rounded-3xl bg-white/70 p-5">
        <h3 className="font-bold text-plum">Te alcanza para</h3>
        {available.length === 0 && <p className="text-sm text-plum-light">Todavía nada, ¡seguí sumando!</p>}
        <ul className="mt-1 space-y-1">
          {available.map((r) => <li key={r.name} className="flex justify-between"><span>{r.name}</span><span>{r.cost} ☕</span></li>)}
          {next.map(({ reward, missing }) => (
            <li key={reward.name} className="flex justify-between text-plum-light/70">
              <span>{reward.name}</span><span>{reward.cost} ☕ · faltan {missing}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-3xl bg-white/70 p-5">
        <h3 className="font-bold text-plum">Movimientos</h3>
        {movements.length === 0 && <p className="text-sm text-plum-light">Sin movimientos todavía.</p>}
        <ul className="mt-1 space-y-1 text-sm">
          {movements.map((m, i) => (
            <li key={`${m.date}-${i}`} className="flex justify-between">
              <span>{m.date.split('-').reverse().slice(0, 2).join('/')} · {m.label}</span>
              <span className={m.amount < 0 ? 'text-coral' : 'text-plum'}>{m.amount > 0 ? `+${m.amount}` : m.amount}</span>
            </li>
          ))}
        </ul>
      </section>

      <form onSubmit={savePhone} className="rounded-3xl bg-white/70 p-5">
        <label className="block text-sm font-bold text-plum" htmlFor="phone">Teléfono (opcional)</label>
        <div className="mt-2 flex gap-2">
          <input id="phone" value={phone} onChange={(e) => { setPhone(e.target.value); setSaved('') }} inputMode="tel" maxLength={30}
            className="w-full rounded-full border border-plum/20 px-4 py-2" />
          <button type="submit" className="rounded-full bg-plum px-4 font-bold text-cream">Guardar</button>
        </div>
        {saved && <p className="mt-1 text-sm text-plum-light">{saved}</p>}
      </form>

      <button type="button" onClick={onLogout} className="w-full text-sm text-plum-light underline">Cerrar sesión</button>
    </div>
  )
}

export default function CafecitosApp() {
  const [loggedIn, setLoggedIn] = useState(Boolean(getToken()))
  const logout = useCallback(() => { clearToken(); setLoggedIn(false) }, [])
  return (
    <main className="mx-auto min-h-screen max-w-md px-5 pb-10">
      <header className="pt-8 text-center">
        <a href="/"><img src="/brand/logo.png" alt="Galia" className="mx-auto h-20 w-auto" /></a>
      </header>
      {loggedIn ? <Wallet onLogout={logout} /> : <Welcome onLoggedIn={() => setLoggedIn(true)} />}
      <p className="mt-8 text-center"><a href="/" className="text-sm text-plum underline">Ver la carta</a></p>
    </main>
  )
}
