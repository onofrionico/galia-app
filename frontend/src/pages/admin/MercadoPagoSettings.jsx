import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posConfigApi, posMpApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { errorMessage } from '@/pos/utils/errors'

const card = 'space-y-3 rounded-xl bg-white p-5 shadow-sm'
const input = 'mt-1 w-full rounded border px-3 py-2'
const primary = 'rounded bg-galia-plum px-4 py-2 text-galia-cream disabled:opacity-50'
const secondary = 'rounded border px-3 py-1.5 text-sm'

// Ajustes → MercadoPago (admin): entorno, token, terminal (modo PDV), webhook y medio de pago del Point.
export default function MercadoPagoSettings() {
  const queryClient = useQueryClient()
  const { data: settings, isLoading, isError } = useQuery({ queryKey: posKeys.mpSettings, queryFn: posMpApi.settings })
  const { data: methods = [] } = useQuery({
    queryKey: ['pos-settings', 'payment-methods'], queryFn: () => posConfigApi.listResource('payment-methods'),
  })
  const [token, setToken] = useState('')
  const [secret, setSecret] = useState('')
  const [terminals, setTerminals] = useState(null)
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)

  const act = async (fn, ok) => {
    setMessage(null)
    setBusy(true)
    try {
      const result = await fn()
      queryClient.invalidateQueries({ queryKey: posKeys.mp })
      setMessage({ ok: true, text: typeof ok === 'function' ? ok(result) : ok })
      return result
    } catch (err) {
      setMessage({ ok: false, text: errorMessage(err) })
      return null
    } finally {
      setBusy(false)
    }
  }

  if (isError) return <p className="p-6 text-red-700">No se pudo cargar la configuración.</p>
  if (isLoading) return <p className="p-6">Cargando…</p>
  // Igual que services/api.js: VITE_API_URL es el origen del backend (sin /api/v1).
  const backend = (import.meta.env.VITE_API_URL || window.location.origin).replace(/\/$/, '')
  const webhookUrl = `${backend}/api/v1/mercadopago/webhook`
  const envLabel = settings.environment === 'test' ? 'prueba' : 'producción'

  const switchEnvironment = (env) => {
    if (env === settings.environment) return
    if (env === 'production' && !window.confirm('Los cobros van a ser reales. ¿Pasar a producción?')) return
    act(() => posMpApi.saveSettings({ environment: env }), 'Entorno cambiado')
  }

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-3xl">MercadoPago</h1>
      {settings.environment === 'test' && (
        <p className="rounded-lg bg-amber-50 p-3 text-amber-900">Modo prueba: los cobros no son reales.</p>
      )}
      {settings.missing.length > 0 && (
        <p className="rounded-lg bg-red-50 p-3 text-red-800">Falta: {settings.missing.join(', ')}</p>
      )}
      {message && (
        <p className={`rounded-lg p-3 ${message.ok ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>{message.text}</p>
      )}

      <section className={card}>
        <h2 className="text-lg font-semibold">1. Entorno y token</h2>
        <div className="flex gap-2">
          {[['test', 'Prueba'], ['production', 'Producción']].map(([env, label]) => (
            <button key={env} type="button" disabled={busy} onClick={() => switchEnvironment(env)}
              className={`rounded px-3 py-1.5 text-sm ${settings.environment === env ? 'bg-galia-plum text-galia-cream' : 'bg-gray-100'}`}>
              {label}
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-600">
          Token de prueba: {settings.has_test_token ? 'cargado' : 'falta'} · Token de producción: {settings.has_prod_token ? 'cargado' : 'falta'}
          {settings.user_id ? ` · Cuenta ${settings.user_id}` : ''}
        </p>
        <label className="block text-sm">Access token ({envLabel})
          <input type="password" autoComplete="off" className={input} value={token}
            onChange={(e) => setToken(e.target.value)} placeholder="APP_USR-…" />
        </label>
        <button type="button" className={primary} disabled={busy || !token.trim()}
          onClick={() => act(() => posMpApi.saveToken(settings.environment, token.trim()), 'Token guardado y verificado')
            .then((r) => r && setToken(''))}>
          Guardar token
        </button>
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">2. Terminal</h2>
        <p className="text-sm">Terminal en uso: <span className="font-mono">{settings.terminal_id ?? '—'}</span></p>
        <button type="button" className={secondary} disabled={busy}
          onClick={() => act(posMpApi.terminals, (t) => (t.length ? 'Terminales encontradas' : 'La cuenta no tiene terminales'))
            .then((t) => t && setTerminals(t))}>
          Buscar terminales
        </button>
        {terminals && (
          <ul className="divide-y text-sm">
            {terminals.map((t) => (
              <li key={t.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                <span className="font-mono">{t.id} · {t.operating_mode ?? '—'}</span>
                <span className="flex gap-3">
                  {t.operating_mode !== 'PDV' && (
                    <button type="button" className="underline" disabled={busy}
                      onClick={() => act(() => posMpApi.setPdv(t.id), (r) => r.message)}>Pasar a modo PDV</button>
                  )}
                  <button type="button" className="underline" disabled={busy}
                    onClick={() => act(() => posMpApi.saveSettings({ terminal_id: t.id }), 'Terminal elegida')}>Usar esta</button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">3. Avisos (webhook)</h2>
        <p className="text-sm">URL para cargar en el panel de MercadoPago (evento de órdenes):</p>
        <p className="break-all rounded bg-gray-100 p-2 font-mono text-xs">{webhookUrl}</p>
        <label className="block text-sm">Clave secreta {settings.has_webhook_secret ? '(cargada)' : '(falta)'}
          <input type="password" autoComplete="off" className={input} value={secret} onChange={(e) => setSecret(e.target.value)} />
        </label>
        <button type="button" className={primary} disabled={busy || !secret.trim()}
          onClick={() => act(() => posMpApi.saveSettings({ webhook_secret: secret.trim() }), 'Clave guardada').then((r) => r && setSecret(''))}>
          Guardar clave
        </button>
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">4. Medio de pago del Point y prueba</h2>
        <select className={input} value={settings.point_payment_method_id ?? ''} disabled={busy}
          onChange={(e) => act(() => posMpApi.saveSettings({ point_payment_method_id: e.target.value ? Number(e.target.value) : null }),
            'Medio de pago guardado')}>
          <option value="">Elegí el medio "MercadoPago Point"</option>
          {methods.filter((m) => m.is_active).map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
        <p className="text-xs text-gray-500">
          Si no existe, crealo en Ajustes del POS → Medios de pago (tipo Tarjeta, con "Es de MercadoPago" y "Lo factura otro sistema").
        </p>
        <button type="button" className={secondary} disabled={busy}
          onClick={() => act(posMpApi.testConnection, (r) => `Conectado · cuenta ${r.account} · terminal ${r.terminal}`)}>
          Probar conexión
        </button>
      </section>
    </div>
  )
}
