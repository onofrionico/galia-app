import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import loyaltyService from '../../services/loyaltyService'
import { ErrorText, button, input, loyaltyKeys, useLoyaltyMutation } from './shared'

export default function SettingsTab() {
  const { data: settings } = useQuery({ queryKey: loyaltyKeys.settings, queryFn: loyaltyService.getSettings })
  const [days, setDays] = useState('')
  useEffect(() => { if (settings) setDays(String(settings.active_days)) }, [settings])
  const save = useLoyaltyMutation(() => loyaltyService.updateSettings(Number(days)))
  return (
    <form className="max-w-md space-y-2" onSubmit={(e) => { e.preventDefault(); save.mutate() }}>
      <label className="block">
        <span className="font-medium">Período de cliente activo</span>
        <span className="block text-sm text-gray-600">Un cliente es activo si vino al menos una vez en estos días.</span>
        <span className="mt-1 flex items-center gap-2">
          <input className={`${input} w-24`} type="number" min="1" max="365" value={days} onChange={(e) => setDays(e.target.value)} /> días
        </span>
      </label>
      <button type="submit" className={button(true)} disabled={save.isPending}>Guardar</button>
      {save.isSuccess && <p className="text-sm text-green-700">Guardado.</p>}
      <ErrorText>{save.errorText}</ErrorText>
    </form>
  )
}
