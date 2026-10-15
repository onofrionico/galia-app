import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posFiscalApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { errorMessage } from '@/pos/utils/errors'

const ENVS = [['homologacion', 'Homologación (pruebas)'], ['produccion', 'Producción']]
const CONDITIONS = [['monotributo', 'Monotributo (Factura C)'], ['responsable_inscripto', 'Responsable inscripto (Factura A/B)']]
const card = 'space-y-3 rounded-xl bg-white p-5 shadow-sm'
const input = 'mt-1 w-full rounded border px-3 py-2'

function download(name, text) {
  const url = URL.createObjectURL(new Blob([text], { type: 'application/pkcs10' }))
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

// Ajustes → Facturación (admin): emisor, punto de venta, certificado por entorno, entorno activo y prueba.
export default function FiscalSettings() {
  const queryClient = useQueryClient()
  const { data: settings, isLoading, isError } = useQuery({ queryKey: posKeys.fiscalSettings, queryFn: posFiscalApi.settings })
  const [form, setForm] = useState(null)
  const [certEnv, setCertEnv] = useState('homologacion')
  const [certificate, setCertificate] = useState('')
  const [message, setMessage] = useState(null)

  useEffect(() => {
    if (settings) {
      setForm({
        cuit: settings.cuit ?? '', business_name: settings.business_name ?? '', address: settings.address ?? '',
        gross_income: settings.gross_income ?? '', activity_start: settings.activity_start ?? '',
        iva_condition: settings.iva_condition, point_of_sale: settings.point_of_sale ?? '',
        cf_id_threshold: settings.cf_id_threshold ?? '', default_iva_rate: String(Number(settings.default_iva_rate)),
      })
    }
  }, [settings])

  const act = async (fn, ok) => {
    setMessage(null)
    try {
      const result = await fn()
      queryClient.invalidateQueries({ queryKey: posKeys.fiscalSettings })
      setMessage({ ok: true, text: typeof ok === 'function' ? ok(result) : ok })
      return result
    } catch (err) {
      setMessage({ ok: false, text: errorMessage(err) })
      return null
    }
  }

  if (isError) return <p className="p-6 text-red-700">No se pudo cargar la configuración.</p>
  if (isLoading || !form) return <p className="p-6">Cargando…</p>
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })
  const saveEmitter = () => act(() => posFiscalApi.saveSettings({
    ...form,
    point_of_sale: form.point_of_sale === '' ? undefined : Number(form.point_of_sale),
    cf_id_threshold: form.cf_id_threshold === '' ? null : form.cf_id_threshold,
  }), 'Datos guardados')
  const creds = settings.credentials[certEnv]
  const switchEnv = (env) => {
    if (env === settings.environment) return
    if (env === 'produccion' && !window.confirm('Las facturas van a tener validez fiscal. ¿Pasar a producción?')) return
    act(() => posFiscalApi.saveSettings({ environment: env }), 'Entorno cambiado')
  }

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-3xl">Facturación</h1>
      {settings.environment === 'homologacion' && (
        <p className="rounded-lg bg-amber-50 p-3 text-amber-900">Modo pruebas (homologación): las facturas no tienen validez fiscal.</p>
      )}
      {settings.missing.length > 0 && (
        <p className="rounded-lg bg-red-50 p-3 text-red-800">Falta: {settings.missing.join(', ')}</p>
      )}
      {message && <p className={`rounded-lg p-3 ${message.ok ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>{message.text}</p>}

      <section className={card}>
        <h2 className="text-lg font-semibold">1. Emisor y punto de venta</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="text-sm">CUIT<input className={input} value={form.cuit} onChange={set('cuit')} /></label>
          <label className="text-sm">Razón social<input className={input} value={form.business_name} onChange={set('business_name')} /></label>
          <label className="text-sm">Domicilio comercial<input className={input} value={form.address} onChange={set('address')} /></label>
          <label className="text-sm">Ingresos brutos<input className={input} value={form.gross_income} onChange={set('gross_income')} /></label>
          <label className="text-sm">Inicio de actividades<input type="date" className={input} value={form.activity_start} onChange={set('activity_start')} /></label>
          <label className="text-sm">Condición frente al IVA
            <select className={input} value={form.iva_condition} onChange={set('iva_condition')}>
              {CONDITIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
          <label className="text-sm">Punto de venta (RECE – web services)
            <input type="number" min="1" className={input} value={form.point_of_sale} onChange={set('point_of_sale')} />
          </label>
          <label className="text-sm">Identificar al consumidor final desde $
            <input type="number" min="0" className={input} value={form.cf_id_threshold} onChange={set('cf_id_threshold')} />
          </label>
          <label className="text-sm">Alícuota de IVA (solo A/B)
            <select className={input} value={form.default_iva_rate} onChange={set('default_iva_rate')}>
              {['0', '10.5', '21', '27'].map((r) => <option key={r} value={r}>{r.replace('.', ',')}%</option>)}
            </select>
          </label>
        </div>
        <p className="text-xs text-gray-500">El punto de venta se da de alta en ARCA como "RECE para aplicativo y web services".</p>
        <button type="button" className="rounded bg-galia-plum px-4 py-2 text-galia-cream" onClick={saveEmitter}>Guardar</button>
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">2. Certificado</h2>
        <div className="flex gap-2">
          {ENVS.map(([env, label]) => (
            <button key={env} type="button" onClick={() => setCertEnv(env)}
              className={`rounded px-3 py-1.5 text-sm ${certEnv === env ? 'bg-galia-plum text-galia-cream' : 'bg-gray-100'}`}>{label}</button>
          ))}
        </div>
        <p className="text-sm text-gray-700">
          {creds.has_certificate
            ? `Certificado cargado. Vence el ${new Date(creds.expires_at).toLocaleDateString('es-AR')}.`
            : 'Sin certificado.'}
          {creds.expires_soon && <span className="ml-2 font-semibold text-red-700">Vence pronto: generá uno nuevo.</span>}
        </p>
        <ol className="list-decimal space-y-2 pl-5 text-sm">
          <li>
            <button type="button" className="underline"
              onClick={() => {
                if (creds.has_certificate && !window.confirm('Generar un pedido nuevo reemplaza la clave y deja sin efecto el certificado actual de este entorno. ¿Seguir?')) return
                act(() => posFiscalApi.generateCsr(certEnv), 'Pedido generado y descargado')
                  .then((csr) => csr && download(`galia-${certEnv}.csr`, csr))
              }}>
              Generar pedido de certificado (CSR)
            </button>{' '}
            y subilo en ARCA: {certEnv === 'homologacion' ? 'WSASS (homologación)' : '"Administración de certificados digitales"'}, asociándolo al servicio de facturación electrónica (wsfe).
          </li>
          <li>
            Pegá el certificado que te da ARCA:
            <textarea rows={6} className={`${input} font-mono text-xs`} value={certificate} onChange={(e) => setCertificate(e.target.value)}
              placeholder="-----BEGIN CERTIFICATE-----" />
            <button type="button" className="mt-2 rounded bg-galia-plum px-4 py-2 text-galia-cream"
              onClick={() => act(() => posFiscalApi.saveCertificate(certEnv, certificate), 'Certificado guardado').then((r) => r && setCertificate(''))}>
              Guardar certificado
            </button>
          </li>
        </ol>
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">3. Entorno y prueba</h2>
        <div className="flex flex-wrap gap-2">
          {ENVS.map(([env, label]) => (
            <button key={env} type="button" onClick={() => switchEnv(env)}
              className={`rounded px-3 py-1.5 text-sm ${settings.environment === env ? 'bg-galia-plum text-galia-cream' : 'bg-gray-100'}`}>{label}</button>
          ))}
          <button type="button" className="ml-auto rounded border px-3 py-1.5 text-sm"
            onClick={() => act(posFiscalApi.testConnection, (r) => `Conectado. ${r.label}`)}>Probar conexión</button>
        </div>
      </section>
    </div>
  )
}
