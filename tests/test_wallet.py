"""Test wallet"""
import pytest
from bigchaindb_wallet.wallet import (
    _encrypt_master_privkey,
    _decrypt_master_privkey,
    get_master_privkey
)


@pytest.mark.parametrize(
    'msg, password',
    [(b'msg', b'password'),
     (b'xxxxx', b'yyyyy'),
     (b'', b''),
     (b'\x00', b'\x00'),
     (b'\xff' * 10, b'\xff' * 10)])
def test_can_decrypt(msg, password):
    crypt, salt = _encrypt_master_privkey(msg, password)
    decr = _decrypt_master_privkey(crypt, password, salt)
    assert decr == msg


def test_get_master_privkey(default_wallet, default_password, master_xpriv):
    xprivkey = get_master_privkey(
        default_wallet, 'default', default_password
    )
    assert master_xpriv == xprivkey
