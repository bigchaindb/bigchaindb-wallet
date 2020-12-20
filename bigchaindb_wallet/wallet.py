import json
from base58 import b58encode, b58decode
from bip32 import BIP32
from mnemonic import Mnemonic
from bigchaindb_driver.crypto import generate_keypair
from nacl import utils, secret
from nacl.pwhash import SCRYPT_SALTBYTES as SALTBYTES
from nacl.pwhash import kdf_scryptsalsa208sha256 as kdf


class WalletError(Exception):
    """Exceptions safe to show in output."""


BIGCHAINDB_COINTYPE = 822
BDBW_PATH_TEMPLATE = ('m/44/{cointype}\'/{{account}}\'/0/{{address_index}}\''
                      .format(cointype=BIGCHAINDB_COINTYPE))


SUPPORTED_LANGUAGES = [
    'cinese-simplified',
    'chinese-traditional',
    'english',
    'french',
    'italian',
    'japanese',
    'korean',
    'spanish',
]


def format_drv_path(account: int, address_index: int):
    return (BDBW_PATH_TEMPLATE
            .format(account=account, address_index=address_index))


def wallet_dumps(wallet_dict):
    return json.dumps(wallet_dict, sort_keys=True, indent=4)


def wallet_dump(wallet_dict, file_location):
    # XXX check whether wallet already exist XXX
    with open(file_location, 'w') as f:
        f.write(wallet_dumps(wallet_dict))


def _encrypt_master_privkey(msg, password):
    salt = utils.random(SALTBYTES)
    encrypted = secret.SecretBox(
        kdf(secret.SecretBox.KEY_SIZE, password, salt)
    ).encrypt(msg)
    return encrypted, salt


def _decrypt_master_privkey(key, password, salt):
    return secret.SecretBox(
        kdf(secret.SecretBox.KEY_SIZE, password, salt)
    ).decrypt(key)


def _get_wallet_account(wallet_dict, wallet_name):
    try:
        return wallet_dict[wallet_name]
    except KeyError:
        raise WalletError('Account {} is not found'.format(wallet_name))


def get_master_privkey(wallet_dict, wallet_name: str, password: str) -> str:
    wallet = _get_wallet_account(wallet_dict, wallet_name)
    try:
        master_privkey = wallet['master_privkey']
        xprivkey = _decrypt_master_privkey(
            b58decode(master_privkey['key']),
            password.encode(),
            b58decode(master_privkey['salt'])
        )
        return xprivkey.decode()
    except KeyError:
        raise WalletError('Account {} contains errors'.format(wallet_name))


def get_master_pubkey(wallet_dict, wallet_name):
    wallet = _get_wallet_account(wallet_dict, wallet_name)
    try:
        return b58decode(wallet['master_pubkey'])
    except KeyError:
        raise WalletError('Account {} contains errors'.format(wallet_name))


def make_mnemonic_phrase(strength=256, language='english', with_entropy=None):
    if language not in SUPPORTED_LANGUAGES:
        raise WalletError('{} not found in supported languages: {}'
                          .format(language, SUPPORTED_LANGUAGES))
    mnemonic_gen = Mnemonic(language)
    if with_entropy:
        # TODO check that strength corresponds to entropy length
        mnemonic_phrase = mnemonic_gen.to_mnemonic(with_entropy)
    else:
        mnemonic_phrase = mnemonic_gen.generate(strength=strength)
    return mnemonic_phrase


def make_extended_key(mnemonic_phrase):
    return BIP32.from_seed(
        Mnemonic.to_seed(mnemonic_phrase)
    )


def make_wallet_dict(xkey: BIP32, password):
    def _value_encode(val):
        return b58encode(val).decode()
    master_privkey_crypt, salt = _encrypt_master_privkey(
        xkey.master_privkey,
        password.encode(),
    )

    return {
        "default": {
            "chain_code": _value_encode(xkey.master_chaincode),
            "master_pubkey": _value_encode(xkey.master_pubkey),
            "master_privkey": {
                'format': 'cryptsalsa208sha256base58',
                'salt': _value_encode(salt),
                'key': _value_encode(master_privkey_crypt)
            }
        }
    }


class ExtendedKey:
    """BigchainDB wrapper arround BIP32."""

    def __init__(self, xkey: BIP32):
        self._xkey = xkey
        self.bdb_keypair = generate_keypair(self.secp256k1_privkey)

    @staticmethod
    def from_seed(seed):
        return ExtendedKey(BIP32.from_seed(seed))

    @property
    def secp256k1_privkey(self):
        self._xkey.master_privkey

    @property
    def secp256k1_pubkey(self):
        self._xkey.master_pubkey

    @staticmethod
    def from_extended_privkey(privkey):
        return ExtendedKey(BIP32.from_xpriv(privkey))

    @staticmethod
    def from_extended_pubkey(pubkey):
        return ExtendedKey(BIP32.from_xpub(pubkey))

    def derive_privkey(self, account=0, address=0):
        return ExtendedKey.from_extended_privkey(
            self._xkey.get_xpriv_from_path(format_drv_path(account, address))
        )

    def derive_pubkey(self, account=0, address=0):
        return ExtendedKey.from_extended_pubkey(
            self._xkey.get_xpub_from_path(format_drv_path(account, address))
        )
