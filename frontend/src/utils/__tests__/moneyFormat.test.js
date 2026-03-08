import { formatMoney, parseMoney, formatMoneyWithCurrency } from '../moneyFormat';

describe('formatMoney', () => {
  test('formats basic amount', () => {
    expect(formatMoney(1234.56)).toBe('1.234,56');
  });

  test('formats large amount', () => {
    expect(formatMoney(1234567.89)).toBe('1.234.567,89');
  });

  test('formats small amount', () => {
    expect(formatMoney(100)).toBe('100,00');
  });

  test('formats zero', () => {
    expect(formatMoney(0)).toBe('0,00');
  });

  test('formats negative amount', () => {
    expect(formatMoney(-1234.56)).toBe('-1.234,56');
  });

  test('formats null as zero', () => {
    expect(formatMoney(null)).toBe('0,00');
  });

  test('formats undefined as zero', () => {
    expect(formatMoney(undefined)).toBe('0,00');
  });

  test('formats empty string as zero', () => {
    expect(formatMoney('')).toBe('0,00');
  });

  test('formats string number', () => {
    expect(formatMoney('1234.56')).toBe('1.234,56');
  });

  test('formats very large number', () => {
    expect(formatMoney(1000000000.50)).toBe('1.000.000.000,50');
  });
});

describe('parseMoney', () => {
  test('parses basic amount', () => {
    expect(parseMoney('1.234,56')).toBe(1234.56);
  });

  test('parses large amount', () => {
    expect(parseMoney('1.234.567,89')).toBe(1234567.89);
  });

  test('parses small amount', () => {
    expect(parseMoney('100,00')).toBe(100);
  });

  test('parses zero', () => {
    expect(parseMoney('0,00')).toBe(0);
  });

  test('parses negative amount', () => {
    expect(parseMoney('-1.234,56')).toBe(-1234.56);
  });

  test('parses empty string as zero', () => {
    expect(parseMoney('')).toBe(0);
  });

  test('parses null as zero', () => {
    expect(parseMoney(null)).toBe(0);
  });

  test('parses number directly', () => {
    expect(parseMoney(1234.56)).toBe(1234.56);
  });

  test('parses invalid string as zero', () => {
    expect(parseMoney('invalid')).toBe(0);
  });
});

describe('formatMoneyWithCurrency', () => {
  test('formats with default currency', () => {
    expect(formatMoneyWithCurrency(1234.56)).toBe('$ 1.234,56');
  });

  test('formats with custom currency', () => {
    expect(formatMoneyWithCurrency(1234.56, 'USD')).toBe('USD 1.234,56');
  });

  test('formats with euro symbol', () => {
    expect(formatMoneyWithCurrency(1234.56, '€')).toBe('€ 1.234,56');
  });
});

describe('round trip', () => {
  test('format and parse returns original value', () => {
    const original = 1234567.89;
    const formatted = formatMoney(original);
    const parsed = parseMoney(formatted);
    expect(parsed).toBeCloseTo(original, 2);
  });

  test('format and parse negative value', () => {
    const original = -1234.56;
    const formatted = formatMoney(original);
    const parsed = parseMoney(formatted);
    expect(parsed).toBeCloseTo(original, 2);
  });
});
