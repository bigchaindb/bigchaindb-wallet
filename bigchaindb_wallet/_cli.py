# TODO Disallow empty passwords
import os
import json
import click
from bigchaindb_driver.offchain import fulfill_transaction
from bigchaindb_driver import BigchainDB
from bigchaindb_wallet.wallet import (
    ExtendedKey,
    WalletError,
    get_master_privkey,
    get_master_pubkey,
    make_extended_key,
    make_mnemonic_phrase,
    make_wallet_dict,
    wallet_dump,
    wallet_dumps,
)




_DEFAULT_KEYSTORE_FILENAME = ".bigchaindb_wallet"

def _get_home_path_and_warn():
    home_path = os.environ.get('HOME')
    if home_path is None:
        home_path = '.'
        click.echo('Warning: HOME path is not set.')
    return home_path

def _get_wallet_content():
    try:
        # TODO convert to Path object
        location = ('{}/{}'.format(_get_home_path_and_warn(),
                                   _DEFAULT_KEYSTORE_FILENAME))
        with open(location) as f:
            return json.loads(f.read())
    except OSError:
        raise WalletError('Wallet not found')


def _get_private_key_drv(name, address, index, password):
    wallet_dict = _get_wallet_content()
    privkey = get_master_privkey(wallet_dict, name, password)
    return (ExtendedKey
            .from_extended_privkey(privkey)
            .derive_privkey(address, index))


def _get_public_key_drv(name, address, index, password):
    wallet_cont = _get_wallet_content()
    pubkey = get_master_pubkey(wallet_cont, name)
    privkey = get_master_privkey(wallet_cont, name, password)
    # ???
    # We'll need the private key at some point anyway, so let's derive
    # everything from private keys.
    return (ExtendedKey
            .from_extended_privkey(privkey)  # privkey?
            .derive_pubkey(address, index))


@click.group()
def cli():
    return

# TODO add option not to store master key?
@cli.command()
@click.option(
    '-s', '--strength', type=int, default=256,
    help=('Seed strength. One of the following [128, 160, 192, 224, 256]'
          ' default is 256')
)
@click.option(
    '-p', '--password', type=str, required=True,
    help=('Wallet master password.  Used to encrypt private keys'))
@click.option(
    '-e', '--entropy', type=str,
    help='Entropy to use for seed generation. It must be base64 encoded'
)
@click.option(
    '-l', '--mnemonic-language', type=str, default='english',
    help=('Mnemonic language. Currengly supported languages: '
          '[cinese-simplified, chinese-traditional, english, french, italian, '
          'japanese, korean, spanish]')
)
@click.option(
    '-o', '--no-keystore', type=bool, is_flag=True,
    help=('Do not create keystore file. Ouput result to stdout'))
@click.option(
    '-q', '--quiet', type=bool, is_flag=True,
    help=('Only ouput the resulting mnemonic seed')
)
@click.option(
    '-L', '--location',
    help=('Keystore file location')
)
def init(strength, entropy, mnemonic_language, no_keystore, location,
         password, quiet):
    # TODO make OS checks
    # TODO no-keystore and quiet should be mutually exclusive?
    try:
        mnemonic_phrase = make_mnemonic_phrase(
            strength, mnemonic_language, entropy
        )
        wallet = make_wallet_dict(
            make_extended_key(mnemonic_phrase), password
        )
        if no_keystore:
            click.echo(wallet_dumps(wallet))
        else:
            # TODO make OS checks: ceck wether directory or file
            if not location:
                location = '{}/{}'.format(_get_home_path_and_warn(),
                                          _DEFAULT_KEYSTORE_FILENAME)
                wallet_dump(wallet, location)
        if quiet:
            click.echo(mnemonic_phrase)
        else:
            click.echo('Keystore initialized in {}'.format(location))
            click.echo('Your mnemonic phrase is \n{}'
                       'Keep it in a safe place'.format(mnemonic_phrase))
    # TODO WalletError decorator
    except WalletError as error:
        click.echo(error)
    except Exception as err:
        click.echo('Operation aborted: unrecoverable error')


@cli.command()
@click.option('-n', '--name', type=str, help='Wallet to use')
@click.option('-a', '--address', default=0, type=int, help='Address to use')
@click.option('-i', '--index', default=0, type=int, help='Address index')
@click.option('-p', '--password', type=str, help='Root account password')
@click.option('-A', '--asset', type=str, help='Asset')
@click.option('-M', '--metadata', type=str, help='Metadata')
@click.option('-I', '--indent', type=bool, help='Indent result', is_flag=True)
def create(name, address, index, password, asset, metadata, indent):
    key = _get_private_key_drv(name, address, index, password)
    bdb = BigchainDB()
    prepared_creation_tx = bdb.transactions.prepare(
        operation='CREATE',
        signers=key.bdb_keypair.public_key,
        asset=json.loads(asset),
        metadata=json.loads(metadata),
    )
    try:
        tx = fulfill_transaction(
            prepared_creation_tx,
            private_keys=[key.bdb_keypair.private_key]
        )
        click.echo(json.dumps(tx, indent=4 if indent else False))
    # TODO WalletError decorator
    except WalletError as error:
        click.echo(error)
    except json.JSONDecodeError:
        click.echo('Operation aborted during transaction parsing')
    except Exception as err:
        click.echo('Operation aborted: unrecoverable error: {}'.format(err))


# TODO address aliases?
# TODO add option to use the derivation path?
@cli.command()
@click.option('-n', '--name', type=str, help='Wallet to use')
@click.option('-a', '--address', default=0, type=int, help='Address to use')
@click.option('-i', '--index', default=0, type=int, help='Address index')
@click.option('-p', '--password', type=str, help='Root account password')
def sign(name, address, password, index):
    try:
        xprivkey = _get_private_key_drv(name, address, index, password)
        tx = fulfill_transaction(
            json.loads(click.get_binary_stream('stdin').encode()),
            private_keys=[xprivkey.bdb_keypair.private_key]
        )
        click.echo(json.dumps(tx))
    # TODO WalletError decorator
    except WalletError as error:
        click.echo(error)
    except json.JSONDecodeError:
        click.echo('Operation aborted during transaction parsing')
    except Exception:
        click.echo('Operation aborted: unrecoverable error')
