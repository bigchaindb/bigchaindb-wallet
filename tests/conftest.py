"""BigchainDB wallet conftest"""
import json
import os
from collections import namedtuple

import pytest
from base58 import b58encode
from bip32 import BIP32
from click.testing import CliRunner

from bigchaindb_wallet.wallet import BDBW_PATH_TEMPLATE


@pytest.fixture
def click_runner(scope='session'):
    return CliRunner()


@pytest.fixture
def seed():
    return b'test' * 8


@pytest.fixture
def keypair_obj(seed):
    return BIP32.from_seed(seed)


@pytest.fixture
def master_xpriv(keypair_obj):
    return keypair_obj.get_master_xpriv()


@pytest.fixture
def master_xpub(keypair_obj):
    return keypair_obj.get_master_xpub()


@pytest.fixture
def default_password():
    return 'DEFAULT PASSWORD'


@pytest.fixture
def privkey_crypt_salt(keypair_obj, default_password):
    from bigchaindb_wallet.wallet import _encrypt_master_privkey
    crypt, salt = _encrypt_master_privkey(
        keypair_obj.get_master_xpriv().encode(),
        default_password.encode()
    )
    return crypt, salt


@pytest.fixture
def bdbw_master_xkey(keypair_obj):
    path = BDBW_PATH_TEMPLATE.format(account=0, address_index=0)
    return namedtuple('BDBWMasterXKeyPair', ['privkey', 'pubkey'])(
        keypair_obj.get_xpriv_from_path(path),
        keypair_obj.get_xpub_from_path(path)
    )


@pytest.fixture
def default_wallet(master_xpub, privkey_crypt_salt):
    return {
        'default': {
            # 'chain_code': key,  # moved to privkey
            'master_pubkey': master_xpub,
            'master_privkey': {
                'format': 'cryptsalsa208sha256base58',
                'key': b58encode(privkey_crypt_salt[0]).decode(),
                'salt': b58encode(privkey_crypt_salt[1]).decode(),
            },
        }
    }


# ??? Can we use yeld from in pytest?
@pytest.fixture
def tmp_home_session(tmp_path, scope='session'):
    home_env_before = os.environ.get('HOME', '')
    os.environ['HOME'] = str(tmp_path)
    yield tmp_path
    os.environ['HOME'] = home_env_before


@pytest.fixture
def tmp_home(tmp_path, scope='function'):
    home_env_before = os.environ.get('HOME', '')
    os.environ['HOME'] = str(tmp_path)
    yield tmp_path
    os.environ['HOME'] = home_env_before


@pytest.fixture
def session_wallet(tmp_home_session, default_wallet):
    with open(tmp_home_session / '.bigchaindb_wallet', 'w') as f:
        json.dump(default_wallet, f)
    return tmp_home_session


@pytest.mark.skip
@pytest.fixture
def fulfilled_hello_world_tx():
    return {
        'id': 'afd0396114d0a7665e81f15d0b6d879f0b31ca1f31bd48531f3452fa2f1e8b55',
        'version': '2.0',
        'inputs': [{
            'fulfillment': 'pGSAIG3OrWZAcCnyIOLKUpD_pEtiZA2Gp-WEZ3q8HVsyIQ32gUD'
            'ae96exzWKHtk6ZYLVDIep9k95PwJJ9EbJG8VYohCrTZd7eVygcFCSpYhv0i850Qgnb'
            'fpTuWtnG-vdIwq3FoK',
            'fulfills': None,
            'owners_before': [
                '8PeE5jSaqnyd79qoobNPxQDf2S9sF4arMQR8DiQypQKo'
            ]
        }],
        'operation': 'CREATE',
        'outputs': [{
            'amount': '1',
            'condition': {
                'details': {
                    'public_key': '8PeE5jSaqnyd79qoobNPxQDf2S9sF4arMQR8DiQypQKo',
                    'type': 'ed25519-sha-256'
                },
                'uri': 'ni:///sha-256;5Xu5GNYzydF5AIGPoz3fSkniUzJzuj913XTOvPXTU'
                '-k?fpt=ed25519-sha-256&cost=131072'
            },
            'public_keys': ['8PeE5jSaqnyd79qoobNPxQDf2S9sF4arMQR8DiQypQKo']
        }],
        'asset': {'data': {'hello': 'world'}},
        'metadata': {'meta': 'someta'},
    }
