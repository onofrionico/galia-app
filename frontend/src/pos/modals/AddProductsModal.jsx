import { useEffect, useMemo, useRef, useState } from 'react'
import { MoreHorizontal, RefreshCw } from 'lucide-react'
import { posApi } from '../api/posApi'
import { useCatalog } from '../hooks/usePosQueries'
import { useSaleMutation } from '../hooks/useSaleMutation'
import Chip from '../ui/Chip'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { addedSummary, filterProducts, needsDetail, priceLabel } from '../utils/catalog'
import ProductDetailStep from './ProductDetailStep'

export const saleTitle = (sale) => (sale.table ? sale.table.label : `Mostrador #${sale.number}`)

export default function AddProductsModal({ sale, onClose }) {
  const { data, isLoading, isError, refetch, isFetching } = useCatalog()
  const [query, setQuery] = useState('')
  const [categoryId, setCategoryId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [added, setAdded] = useState([])
  const { run, busy } = useSaleMutation()
  const inputRef = useRef(null)

  const products = useMemo(
    () => filterProducts(data?.products ?? [], { query, categoryId }),
    [data, query, categoryId],
  )

  useEffect(() => {
    if (!detail) inputRef.current?.focus()
  }, [detail])

  const add = async (product, { variantId, quantity = 1, optionIds = [], note = null }) => {
    const result = await run(sale.id, () => posApi.addItem(sale.id, {
      product_variant_id: variantId, quantity, modifier_option_ids: optionIds, note,
    }))
    if (result) {
      setAdded((list) => [...list, { name: product.name, quantity }])
      setDetail(null)
    }
  }

  const choose = (product) => {
    if (needsDetail(product)) setDetail(product)
    else add(product, { variantId: product.variants[0].id })
  }

  const onSearchKey = (event) => {
    if (event.key === 'Enter' && products[0] && !busy) {
      event.preventDefault()
      choose(products[0])
    }
  }

  const footer = (
    <div className="flex items-center justify-between gap-3">
      <span className="text-sm text-gray-600">{addedSummary(added)}</span>
      <button type="button" className={btn('primary')} onClick={onClose}>Listo</button>
    </div>
  )

  return (
    <Modal title={`Agregar a ${saleTitle(sale)}`} onClose={onClose} size="lg" footer={footer}>
      {detail ? (
        <ProductDetailStep product={detail} busy={busy} onBack={() => setDetail(null)}
          onAdd={(choice) => add(detail, choice)} />
      ) : (
        <>
          <input ref={inputRef} value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={onSearchKey}
            placeholder="Buscar producto… (Enter agrega el primero)" aria-label="Buscar producto"
            className="w-full rounded-lg border border-gray-300 px-4 py-3 text-lg focus:border-galia-plum focus:outline-none" />
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Chip active={categoryId === null} onClick={() => setCategoryId(null)}>Todos</Chip>
            {(data?.categories ?? []).map((category) => (
              <Chip key={category.id} active={categoryId === category.id} onClick={() => setCategoryId(category.id)}>
                {category.name}
              </Chip>
            ))}
            <button type="button" onClick={() => refetch()} disabled={isFetching}
              className="ml-auto flex items-center gap-1 text-sm text-gray-600 hover:text-galia-plum">
              <RefreshCw size={14} /> Recargar carta
            </button>
          </div>

          {isLoading && <p className="mt-6 text-center text-gray-500">Cargando carta…</p>}
          {isError && <p className="mt-6 text-center text-red-700">No se pudo cargar la carta.</p>}

          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {products.map((product) => (
              <div key={product.id} className="relative">
                <button type="button" disabled={busy} onClick={() => choose(product)}
                  className="flex h-20 w-full flex-col justify-between rounded-lg border border-gray-300 bg-white p-2 pr-7 text-left hover:border-galia-plum disabled:opacity-50">
                  <span className="line-clamp-2 text-sm font-medium">{product.name}</span>
                  <span className="text-xs text-gray-600">{priceLabel(product)}</span>
                </button>
                <button type="button" aria-label={`Opciones de ${product.name}`} onClick={() => setDetail(product)}
                  className="absolute right-1 top-1 rounded p-1 text-gray-500 hover:bg-gray-100">
                  <MoreHorizontal size={16} />
                </button>
              </div>
            ))}
          </div>
          {!isLoading && products.length === 0 && <p className="mt-6 text-center text-gray-500">Sin resultados.</p>}
        </>
      )}
    </Modal>
  )
}
