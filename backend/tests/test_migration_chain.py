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


def test_pos_base_chain_starts_after_schema_drift_fix():
    revisions = _revisions()
    assert revisions['b1a0_add_permissions_system'] == ['sync_schema_drift']


def test_suppliers_follows_permissions():
    assert _revisions()['b1a1_add_suppliers'] == ['b1a0_add_permissions_system']


def test_products_follows_suppliers():
    assert _revisions()['b1a2_add_products_and_supplies'] == ['b1a1_add_suppliers']


def test_site_config_is_head_of_pos_base_chain():
    assert _revisions()['b1a3_add_site_config'] == ['b1a2_add_products_and_supplies']
