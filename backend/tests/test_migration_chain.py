import os
import re

VERSIONS = os.path.join(os.path.dirname(__file__), '..', 'migrations', 'versions')


def _revisions():
    revisions = {}
    for name in os.listdir(VERSIONS):
        if not name.endswith('.py'):
            continue
        text = open(os.path.join(VERSIONS, name), encoding='utf-8').read()
        rev = re.search(r"^revision\s*=\s*['\"]([^'\"]+)", text, re.M).group(1)
        down = re.search(r"^down_revision\s*=\s*(.+)$", text, re.M).group(1)
        revisions[rev] = re.findall(r"['\"]([^'\"]+)['\"]", down)
    return revisions


def test_single_head():
    revisions = _revisions()
    referenced = {d for downs in revisions.values() for d in downs}
    heads = sorted(r for r in revisions if r not in referenced)
    assert len(heads) == 1, heads


def test_pos_base_chain_is_linear_from_menu():
    revisions = _revisions()
    assert revisions['b1a0_add_permissions_system'] == ['add_menu_tables']


def test_suppliers_follows_permissions():
    assert _revisions()['b1a1_add_suppliers'] == ['b1a0_add_permissions_system']
