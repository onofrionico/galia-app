"""Compara las fallas actuales de pytest contra la línea base guardada.

Uso (desde backend/):
    python -m pytest -q -p no:cacheprovider -rfE > /tmp/pytest_out.txt
    python scripts/compare_baseline.py /tmp/pytest_out.txt ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt

Sale con código 1 si hay fallas o errores que no están en la línea base.
"""
import re
import sys


def failures(path):
    pattern = re.compile(r'^(FAILED|ERROR) (\S+)')
    result = set()
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            match = pattern.match(line.strip())
            if match:
                result.add(f'{match.group(1)} {match.group(2).replace(chr(92), "/")}')
    return result


def main():
    current = failures(sys.argv[1])
    baseline = failures(sys.argv[2])
    new = sorted(current - baseline)
    fixed = sorted(baseline - current)
    print(f'Fallas actuales: {len(current)} | línea base: {len(baseline)}')
    if fixed:
        print(f'Ya no fallan ({len(fixed)}):')
        for item in fixed:
            print('  ', item)
    if new:
        print(f'FALLAS NUEVAS ({len(new)}):')
        for item in new:
            print('  ', item)
        sys.exit(1)
    print('Sin fallas nuevas.')


if __name__ == '__main__':
    main()
