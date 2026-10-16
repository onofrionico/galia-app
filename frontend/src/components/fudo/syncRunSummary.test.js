import { describe, expect, it } from 'vitest';
import { isRunFinished, summarizeRun, validateRange } from './syncRunSummary';

describe('validateRange', () => {
  it('requires both dates', () => {
    expect(validateRange('', '2026-10-31')).toMatch(/dos fechas/);
    expect(validateRange('2026-10-01', '')).toMatch(/dos fechas/);
  });
  it('rejects inverted ranges', () => {
    expect(validateRange('2026-10-31', '2026-10-01')).toMatch(/posterior/);
  });
  it('rejects ranges over 366 days', () => {
    expect(validateRange('2025-01-01', '2026-10-31')).toMatch(/366/);
  });
  it('accepts a valid range', () => {
    expect(validateRange('2026-10-01', '2026-10-31')).toBeNull();
  });
});

describe('isRunFinished', () => {
  it('is false while running or without a run', () => {
    expect(isRunFinished(null)).toBe(false);
    expect(isRunFinished({ status: 'running' })).toBe(false);
  });
  it('is true for ok and error', () => {
    expect(isRunFinished({ status: 'ok' })).toBe(true);
    expect(isRunFinished({ status: 'error' })).toBe(true);
  });
});

describe('summarizeRun', () => {
  it('lists every stat with 0 for missing ones', () => {
    const rows = summarizeRun({ stats: { created: 3, suppliers_created: 1 } });
    expect(rows.find((r) => r.key === 'created').value).toBe(3);
    expect(rows.find((r) => r.key === 'suppliers_created').value).toBe(1);
    expect(rows.find((r) => r.key === 'updated').value).toBe(0);
    expect(rows).toHaveLength(8);
  });
  it('handles a run without stats', () => {
    expect(summarizeRun({ stats: null }).every((r) => r.value === 0)).toBe(true);
  });
});
