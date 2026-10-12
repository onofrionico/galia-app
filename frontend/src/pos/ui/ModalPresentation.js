import { createContext, useContext } from 'react'

// Cómo se dibujan los modales del POS: 'dialog' (caja, centrados) o 'sheet' (celular, hoja inferior).
export const ModalPresentationContext = createContext('dialog')

export const useModalPresentation = () => useContext(ModalPresentationContext)
