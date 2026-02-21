export const validateDNI = (dni) => {
  if (!dni) return { valid: false, error: 'DNI es requerido' }
  
  const dniClean = dni.toString().replace(/\D/g, '')
  
  if (dniClean.length < 7 || dniClean.length > 8) {
    return { valid: false, error: 'DNI debe tener 7 u 8 dígitos' }
  }
  
  const dniNumber = parseInt(dniClean)
  if (dniNumber < 1000000 || dniNumber > 99999999) {
    return { valid: false, error: 'DNI fuera de rango válido' }
  }
  
  return { valid: true, error: null }
}

export const validateCUIL = (cuil) => {
  if (!cuil) return { valid: true, error: null }
  
  const cuilClean = cuil.replace(/\D/g, '')
  
  if (cuilClean.length !== 11) {
    return { valid: false, error: 'CUIL debe tener 11 dígitos (XX-XXXXXXXX-X)' }
  }
  
  const multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
  let sum = 0
  
  for (let i = 0; i < 10; i++) {
    sum += parseInt(cuilClean[i]) * multipliers[i]
  }
  
  let remainder = sum % 11
  let expectedVerifier = 11 - remainder
  
  if (expectedVerifier === 11) {
    expectedVerifier = 0
  } else if (expectedVerifier === 10) {
    expectedVerifier = 9
  }
  
  const actualVerifier = parseInt(cuilClean[10])
  
  if (actualVerifier !== expectedVerifier) {
    return { valid: false, error: 'Dígito verificador de CUIL inválido' }
  }
  
  return { valid: true, error: null }
}

export const formatCUIL = (value) => {
  const clean = value.replace(/\D/g, '')
  
  if (clean.length <= 2) return clean
  if (clean.length <= 10) return `${clean.slice(0, 2)}-${clean.slice(2)}`
  return `${clean.slice(0, 2)}-${clean.slice(2, 10)}-${clean.slice(10, 11)}`
}

export const validateAge = (birthDate) => {
  if (!birthDate) return { valid: true, error: null }
  
  const today = new Date()
  const birth = new Date(birthDate)
  
  let age = today.getFullYear() - birth.getFullYear()
  const monthDiff = today.getMonth() - birth.getMonth()
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--
  }
  
  if (age < 18) {
    return { valid: false, error: 'El empleado debe tener al menos 18 años' }
  }
  
  return { valid: true, age, error: null }
}

export const validateEmail = (email) => {
  if (!email) return { valid: false, error: 'Email es requerido' }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  
  if (!emailRegex.test(email)) {
    return { valid: false, error: 'Email inválido' }
  }
  
  return { valid: true, error: null }
}

export const validatePhone = (phone) => {
  if (!phone) return { valid: true, error: null }
  
  const phoneClean = phone.replace(/\D/g, '')
  
  if (phoneClean.length < 10) {
    return { valid: false, error: 'Teléfono debe tener al menos 10 dígitos' }
  }
  
  return { valid: true, error: null }
}
