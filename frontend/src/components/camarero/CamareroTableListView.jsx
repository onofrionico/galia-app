import PropTypes from 'prop-types'
import GALIA from '../../constants/colors'

const CamareroTableListView = ({ mesas = [], onMesaClick }) => {
  // Show empty state if no mesas
  if (mesas.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <p style={{ color: GALIA.grisClaro }} className="text-base">
          Sin mesas disponibles
        </p>
      </div>
    )
  }

  return (
    <div className="w-full h-full overflow-y-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-0 bg-white border-b" style={{ borderColor: GALIA.grisLigero }}>
          <tr>
            <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: GALIA.marron }}>
              Mesa
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: GALIA.marron }}>
              Estado
            </th>
            <th className="px-4 py-3 text-right text-sm font-semibold" style={{ color: GALIA.marron }}>
              Total
            </th>
          </tr>
        </thead>
        <tbody>
          {mesas.map((mesa, index) => (
            <tr
              key={mesa.id}
              role="button"
              tabIndex={0}
              onClick={() => onMesaClick(mesa)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onMesaClick(mesa)
                }
              }}
              className="border-b cursor-pointer hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2"
              style={{
                borderColor: GALIA.grisLigero,
                backgroundColor: index % 2 === 0 ? 'white' : GALIA.crema,
                '--tw-ring-color': GALIA.marron
              }}
            >
              <td className="px-4 py-4 text-base font-semibold" style={{ color: GALIA.marron }}>
                {mesa.numero}
              </td>
              <td className="px-4 py-4">
                <span
                  className="inline-block px-3 py-1 rounded-full text-sm font-semibold"
                  aria-label={`Estado: ${mesa.status === 'libre' ? 'Libre' : 'Ocupada'}`}
                  style={{
                    backgroundColor: mesa.status === 'libre' ? GALIA.verde : GALIA.amarillo,
                    color: mesa.status === 'libre' ? 'white' : GALIA.marron
                  }}
                >
                  {mesa.status === 'libre' ? 'Libre' : 'Ocupada'}
                </span>
              </td>
              <td className="px-4 py-4 text-right font-semibold" style={{ color: GALIA.marron }}>
                {mesa.openOrder ? (
                  <div>
                    <div style={{ color: GALIA.amarillo }}>
                      ${parseFloat(mesa.openOrder.total || 0).toFixed(2)}
                    </div>
                    <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                      ({mesa.openOrder.items?.length || 0} ítems)
                    </div>
                  </div>
                ) : (
                  <span style={{ color: GALIA.grisClaro }}>-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

CamareroTableListView.propTypes = {
  mesas: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      numero: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      status: PropTypes.oneOf(['libre', 'ocupada']).isRequired,
      openOrder: PropTypes.shape({
        total: PropTypes.number,
        items: PropTypes.array
      })
    })
  ),
  onMesaClick: PropTypes.func.isRequired
}

CamareroTableListView.defaultProps = {
  mesas: []
}

export default CamareroTableListView
