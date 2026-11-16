from app.services.vouchers.codes import ALPHABET, CODE_LENGTH, format_code, generate_code, normalize_code


def test_generate_code_uses_safe_alphabet_and_length():
    for _ in range(200):
        code = generate_code()
        assert len(code) == CODE_LENGTH == 10
        assert set(code) <= set(ALPHABET)
        assert not set(code) & set('0O1IL')


def test_generate_code_is_not_repeated():
    assert len({generate_code() for _ in range(1000)}) == 1000


def test_format_code():
    assert format_code('ABCDEFGHJK') == 'GAL-ABCDE-FGHJK'


def test_normalize_accepts_any_typing():
    for raw in (' gal-abcde-fghjk ', 'abcdefghjk', 'GAL ABCDE FGHJK'):
        assert normalize_code(raw) == 'ABCDEFGHJK'


def test_normalize_empty():
    assert normalize_code(None) == ''
    assert normalize_code('') == ''
