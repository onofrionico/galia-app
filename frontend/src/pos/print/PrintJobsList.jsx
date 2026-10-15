import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { posPrintApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { timeLabel } from '../utils/time'
import { jobLabel } from './printStatus'

const STATUS = { pending: 'En cola', printing: 'Imprimiendo', printed: 'Impresa', failed: 'Con error' }

// Pestaña "Impresiones" de la venta: lo que se mandó a imprimir y su estado, con reimpresión.
export default function PrintJobsList({ saleId }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const { data: jobs = [], isLoading, isError } = useQuery({
    queryKey: posKeys.printSaleJobs(saleId), queryFn: () => posPrintApi.saleJobs(saleId), refetchInterval: 5_000,
  })
  const reprint = useMutation({
    mutationFn: posPrintApi.reprint,
    onSuccess: () => {
      toast.success('Enviado a imprimir')
      queryClient.invalidateQueries({ queryKey: posKeys.printSaleJobs(saleId) })
    },
    onError: (error) => toast.error(errorMessage(error)),
  })
  if (isLoading) return <p className="p-4 text-sm text-gray-500">Cargando impresiones…</p>
  if (isError && jobs.length === 0) return <p className="p-4 text-sm text-red-700">No se pudieron cargar las impresiones.</p>
  if (jobs.length === 0) return <p className="p-4 text-sm text-gray-500">Todavía no se imprimió nada de esta venta.</p>
  return (
    <ul className="divide-y px-4 py-2">
      {jobs.map((job) => (
        <li key={job.id} className="flex items-center justify-between gap-2 py-2 text-sm">
          <span>
            <span className="font-mono text-gray-500">{timeLabel(job.created_at)}</span> {jobLabel(job)}
            {job.batch ? ` · tanda ${job.batch}` : ''}{job.reprint_of ? ' · reimpresión' : ''}
            <span className={`ml-2 ${job.status === 'failed' ? 'text-red-700' : 'text-gray-500'}`}>{STATUS[job.status]}</span>
          </span>
          <button type="button" className="min-h-[36px] text-galia-plum underline" disabled={reprint.isPending}
            onClick={() => reprint.mutate(job.id)}>Reimprimir</button>
        </li>
      ))}
    </ul>
  )
}
