/**
 * Formatea un monto en formato argentino
 * @param {number|string} amount - Monto a formatear
 * @returns {string} Monto formateado (ej: "1.234,56")
 */
export function formatMoney(amount) {
  if (amount === null || amount === undefined || amount === '') {
    return '0,00';
  }

  let numericAmount;
  try {
    numericAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  } catch (e) {
    return '0,00';
  }

  if (isNaN(numericAmount)) {
    return '0,00';
  }

  const isNegative = numericAmount < 0;
  numericAmount = Math.abs(numericAmount);

  const integerPart = Math.floor(numericAmount);
  let decimalPart = Math.round((numericAmount - integerPart) * 100);

  if (decimalPart === 100) {
    integerPart += 1;
    decimalPart = 0;
  }

  const integerStr = integerPart.toString();
  let formattedInteger = '';

  for (let i = 0; i < integerStr.length; i++) {
    if (i > 0 && (integerStr.length - i) % 3 === 0) {
      formattedInteger += '.';
    }
    formattedInteger += integerStr[i];
  }

  const decimalStr = decimalPart.toString().padStart(2, '0');
  const result = `${formattedInteger},${decimalStr}`;

  return isNegative ? `-${result}` : result;
}

/**
 * Parsea un string en formato argentino a número
 * @param {string} value - String en formato argentino (ej: "1.234,56")
 * @returns {number} Número parseado
 */
export function parseMoney(value) {
  if (!value) {
    return 0;
  }

  if (typeof value === 'number') {
    return value;
  }

  try {
    let valueStr = value.toString().trim();

    const isNegative = valueStr.startsWith('-');
    if (isNegative) {
      valueStr = valueStr.substring(1);
    }

    valueStr = valueStr.replace(/\./g, '');
    valueStr = valueStr.replace(',', '.');

    const result = parseFloat(valueStr);

    if (isNaN(result)) {
      return 0;
    }

    return isNegative ? -result : result;
  } catch (e) {
    return 0;
  }
}

/**
 * Formatea un monto con símbolo de moneda
 * @param {number|string} amount - Monto a formatear
 * @param {string} currency - Símbolo de moneda (default: '$')
 * @returns {string} Monto formateado con símbolo (ej: "$ 1.234,56")
 */
export function formatMoneyWithCurrency(amount, currency = '$') {
  const formatted = formatMoney(amount);
  return `${currency} ${formatted}`;
}
