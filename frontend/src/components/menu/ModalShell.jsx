import { X } from 'lucide-react'

const ModalShell = ({ title, onClose, children, footer }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-stretch sm:items-center justify-center z-50 sm:p-4">
    <div className="bg-white w-full sm:max-w-xl sm:rounded-lg shadow-xl flex flex-col max-h-screen sm:max-h-[90vh]">
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 className="text-lg font-bold text-gray-900">{title}</h2>
        <button type="button" onClick={onClose} className="p-1 text-gray-500 hover:text-gray-700" aria-label="Cerrar">
          <X className="h-5 w-5" />
        </button>
      </div>
      <div className="p-4 overflow-y-auto flex-1">{children}</div>
      {footer && <div className="p-4 border-t border-gray-200 flex flex-wrap gap-2 justify-end">{footer}</div>}
    </div>
  </div>
)

export default ModalShell
