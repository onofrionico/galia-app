import { useState } from 'react'
import { ChevronDown, ChevronRight, ChevronUp, Eye, EyeOff, Pencil, Plus, AlertTriangle, Link2, ImageOff } from 'lucide-react'
import { variantSummary } from '../../utils/menuFormat'

const IconButton = ({ onClick, label, disabled, children }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    aria-label={label}
    title={label}
    className="p-1.5 rounded text-gray-500 hover:text-gray-800 hover:bg-gray-100 disabled:opacity-30 disabled:hover:bg-transparent"
  >
    {children}
  </button>
)

const FudoBadge = ({ variants }) => {
  const linked = variants.filter((v) => v.fudo_product_id)
  if (linked.some((v) => v.fudo_status && v.fudo_status !== 'ok')) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">
        <AlertTriangle className="h-3 w-3" /> Revisar Fudo
      </span>
    )
  }
  if (linked.length === 0) {
    return <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">Precio manual</span>
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs text-green-700 bg-green-50 px-1.5 py-0.5 rounded">
      <Link2 className="h-3 w-3" /> Fudo
    </span>
  )
}

const ItemRow = ({ item, index, total, tagsById, onEdit, onToggle, onMove }) => (
  <li className={`flex items-center gap-3 py-2 px-3 ${item.is_visible ? '' : 'opacity-50'}`}>
    {item.image_url ? (
      <img src={item.image_url} alt="" className="h-12 w-12 rounded object-cover flex-shrink-0" />
    ) : (
      <div className="h-12 w-12 rounded bg-gray-100 flex items-center justify-center flex-shrink-0">
        <ImageOff className="h-4 w-4 text-gray-400" />
      </div>
    )}
    <button type="button" onClick={onEdit} className="flex-1 min-w-0 text-left">
      <div className="font-medium text-gray-900 truncate">
        {item.is_featured && <span className="text-amber-500 mr-1">★</span>}
        {item.name}
      </div>
      <div className="text-sm text-gray-600 truncate">{variantSummary(item.variants)}</div>
      <div className="flex flex-wrap gap-1 mt-1">
        <FudoBadge variants={item.variants} />
        {item.tag_ids.map((id) => tagsById[id] && (
          <span key={id} className="text-xs px-1.5 py-0.5 rounded text-white" style={{ backgroundColor: tagsById[id].color }}>
            {tagsById[id].name}
          </span>
        ))}
      </div>
    </button>
    <div className="flex items-center flex-shrink-0">
      <IconButton label="Subir" onClick={() => onMove(index, -1)} disabled={index === 0}><ChevronUp className="h-4 w-4" /></IconButton>
      <IconButton label="Bajar" onClick={() => onMove(index, 1)} disabled={index === total - 1}><ChevronDown className="h-4 w-4" /></IconButton>
      <IconButton label={item.is_visible ? 'Ocultar' : 'Mostrar'} onClick={onToggle}>
        {item.is_visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
      </IconButton>
    </div>
  </li>
)

const CategoryCard = ({ category, index, total, tagsById, onMove, onEdit, onToggle, onAddItem, onEditItem, onToggleItem, onMoveItem }) => {
  const [open, setOpen] = useState(true)

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${category.is_visible ? '' : 'opacity-60'}`}>
      <div className="flex items-center gap-2 p-3 border-b border-gray-100">
        <button type="button" onClick={() => setOpen(!open)} className="flex items-center gap-2 flex-1 min-w-0 text-left">
          {open ? <ChevronDown className="h-4 w-4 text-gray-500" /> : <ChevronRight className="h-4 w-4 text-gray-500" />}
          <span className="font-semibold text-gray-900 truncate">{category.name}</span>
          <span className="text-sm text-gray-500">({category.items.length})</span>
        </button>
        <IconButton label="Subir categoría" onClick={() => onMove(index, -1)} disabled={index === 0}><ChevronUp className="h-4 w-4" /></IconButton>
        <IconButton label="Bajar categoría" onClick={() => onMove(index, 1)} disabled={index === total - 1}><ChevronDown className="h-4 w-4" /></IconButton>
        <IconButton label={category.is_visible ? 'Ocultar categoría' : 'Mostrar categoría'} onClick={onToggle}>
          {category.is_visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
        </IconButton>
        <IconButton label="Editar categoría" onClick={onEdit}><Pencil className="h-4 w-4" /></IconButton>
        <button
          type="button"
          onClick={onAddItem}
          aria-label="Agregar ítem"
          className="inline-flex items-center gap-1 text-sm px-2 py-1 rounded bg-rose-50 text-rose-700 hover:bg-rose-100"
        >
          <Plus className="h-4 w-4" /> <span className="hidden sm:inline">Ítem</span>
        </button>
      </div>
      {open && (
        <ul className="divide-y divide-gray-100">
          {category.items.length === 0 && <li className="p-3 text-sm text-gray-500">Sin ítems todavía.</li>}
          {category.items.map((item, itemIndex) => (
            <ItemRow
              key={item.id}
              item={item}
              index={itemIndex}
              total={category.items.length}
              tagsById={tagsById}
              onEdit={() => onEditItem(item)}
              onToggle={() => onToggleItem(item)}
              onMove={(i, direction) => onMoveItem(category, i, direction)}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

export default CategoryCard
