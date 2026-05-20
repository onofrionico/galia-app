import { useState, useEffect } from 'react'
import GALIA from '../../constants/colors'
import productCategoriesService from '../../services/productCategoriesService'
import productsService from '../../services/productsService'

const ProductCatalog = ({ onProductSelected, loading = false, error = null }) => {
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [fetchingData, setFetchingData] = useState(true)
  const [fetchError, setFetchError] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [catsRes, prodsRes] = await Promise.all([
        productCategoriesService.getCategories({ include_inactive: false }),
        productsService.getProducts({ per_page: 100, include_inactive: false }),
      ])

      setCategories(catsRes.categories || [])
      setProducts(prodsRes.products || [])

      if (catsRes.categories && catsRes.categories.length > 0) {
        setActiveCategory(catsRes.categories[0].id)
      }
    } catch (err) {
      setFetchError('Error al cargar productos')
    } finally {
      setFetchingData(false)
    }
  }

  const filteredProducts = activeCategory
    ? products.filter((p) => p.category_id === activeCategory && p.is_active)
    : products.filter((p) => p.is_active)

  if (fetchingData) {
    return (
      <div className="flex-1 overflow-y-auto p-4">
        <div className="text-center" style={{ color: GALIA.grisClaro }}>
          Cargando productos...
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
      {/* Category Tabs */}
      <div className="flex gap-2 mb-4 pb-4 border-b overflow-x-auto" style={{ borderColor: GALIA.grisLigero }}>
        <button
          onClick={() => setActiveCategory(null)}
          className={`px-3 py-2 rounded whitespace-nowrap font-medium transition-colors text-sm`}
          style={{
            backgroundColor: activeCategory === null ? GALIA.amarillo : GALIA.grisLigero,
            color: activeCategory === null ? GALIA.marron : GALIA.grisClaro,
          }}
        >
          Todos
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-3 py-2 rounded whitespace-nowrap font-medium transition-colors text-sm`}
            style={{
              backgroundColor: activeCategory === cat.id ? GALIA.amarillo : GALIA.grisLigero,
              color: activeCategory === cat.id ? GALIA.marron : GALIA.grisClaro,
            }}
          >
            {cat.icon || '📦'} {cat.name}
          </button>
        ))}
      </div>

      {/* Products List */}
      <div className="overflow-y-auto flex-1">
        {filteredProducts.length > 0 ? (
          <div className="space-y-2">
            {filteredProducts.map((product) => (
              <button
                key={product.id}
                onClick={() => onProductSelected?.(product)}
                className="w-full flex items-center gap-3 p-3 rounded-lg border-2 hover:shadow-md transition-all text-left"
                style={{
                  borderColor: GALIA.grisLigero,
                  backgroundColor: GALIA.crema,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = GALIA.amarillo
                  e.currentTarget.style.backgroundColor = GALIA.blanco
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = GALIA.grisLigero
                  e.currentTarget.style.backgroundColor = GALIA.crema
                }}
              >
                {/* Image Thumbnail */}
                <div
                  className="w-20 h-20 flex-shrink-0 rounded-lg flex items-center justify-center text-2xl"
                  style={{ backgroundColor: GALIA.grisLigero }}
                >
                  {product.image_url ? (
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="w-full h-full object-cover rounded-lg"
                    />
                  ) : (
                    '📦'
                  )}
                </div>

                {/* Product Info */}
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-sm leading-snug line-clamp-2" style={{ color: GALIA.marron }}>
                    {product.name}
                  </div>
                  {product.category_name && (
                    <div className="text-xs mt-1 line-clamp-1" style={{ color: GALIA.grisClaro }}>
                      {product.category_name}
                    </div>
                  )}
                  {product.variants && product.variants.length > 0 && (
                    <div className="text-xs font-semibold mt-2" style={{ color: GALIA.amarillo }}>
                      ${product.variants[0].price}
                      {product.variants.length > 1 && ` +${product.variants.length - 1}`}
                    </div>
                  )}
                </div>

                {/* Quick Add Indicator */}
                <div className="flex-shrink-0 text-lg" style={{ color: GALIA.amarillo }}>
                  →
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="text-center py-8" style={{ color: GALIA.grisClaro }}>
            <p className="text-sm font-medium">No hay productos disponibles</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ProductCatalog
