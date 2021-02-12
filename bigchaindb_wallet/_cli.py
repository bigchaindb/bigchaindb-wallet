# TODO Disallow empty passwords
import os
import json
import click
from bigchaindb_driver.offchain import fulfill_transaction
from bigchaindb_driver import BigchainDB
import pickledb

import bigchaindb_wallet.keymanagement as km
import bigchaindb_wallet.keystore as ks
from base58 import b58encode


# Decoratoers
_wallet = click.option(
    '-w', '--wallet',
    help='Wallet to use',
    type=str,
    default=lambda: os.environ.get('BDBW_WALLET_NAME', 'default'),
)

_address = click.option(
    '-a', '--address',
    help='Address to use',
    type=int,
    default=lambda: os.environ.get('BDBW_ACCOUNT_IDX', 0)
)

_index = click.option(
    '-i', '--index',
    help='Address index',
    type=int,
    default=lambda: os.environ.get('BDBW_ADDRESS_IDX', 0)
)

_password = click.option(
    '-p', '--password',
    help='Wallet master password.  Used to encrypt and decrypt private keys',
    type=str,
    default=lambda: os.environ.get('BDBW_PASSWORD')
)

_location = click.option(
    '-L', '--location',
    help=('Keystore file location'),
    default=ks.get_home_path_and_warn
)

_transaction = click.option(
    '-t', '--transaction',
    help='Transaction json string',
    type=str,
    required=True
)

_indent = click.option(
    '-I', '--indent',
    help='Indent result',
    type=bool,
    is_flag=True
)



# CLI
@click.group()
def cli():
    return


@cli.command()
@_password
@click.option('-s', '--strength', type=int, default=256,
              help=('Seed strength. One of the following '
                    '[128, 160, 192, 224, 256] default is 256'))
@click.option('-e', '--entropy', type=str,
              help='Entropy to use for seed generation. It must be hex encoded')
@click.option('-l', '--mnemonic-language', type=str, default='english',
              help=('Mnemonic language. Currengly supported languages: '
                    '[cinese-simplified, chinese-traditional, english, french, '
                    'italian, japanese, korean, spanish]'))
@click.option('-o', '--no-keystore', type=bool, is_flag=True,
              help=('Do not create keystore file. Ouput result to stdout'))
@click.option('-q', '--quiet', type=bool, is_flag=True,
              help=('Only ouput the resulting mnemonic seed'))

def init(strength, entropy, mnemonic_language, no_keystore, location,
         password, quiet):
    # TODO make OS checks
    # TODO no-keystore and quiet should be mutually exclusive?
    # TODO Sensible errors on bad input
    # MAYBE mutual exclusion option for click
    try:
        mnemonic_phrase = km.make_mnemonic_phrase(
            strength,
            mnemonic_language,
            bytes.fromhex(entropy) if entropy else None)
        wallet = ks.make_wallet_dict(
            km.seed_to_extended_key(km.mnemonic_to_seed(mnemonic_phrase)),
            password)
        if no_keystore:
            click.echo(ks.wallet_dumps(wallet))
        else:
            # TODO make OS checks: ceck wether directory or file
            if not location:
                location = '{}/{}'.format(ks.get_home_path_and_warn(),
                                          ks.DEFAULT_KEYSTORE_FILENAME)
            else:
                location = ks.DEFAULT_KEYSTORE_FILENAME
            ks.wallet_dump(wallet, location)
        if quiet:
            click.echo(mnemonic_phrase)
        else:
            click.echo('Keystore initialized in {}:'.format(location))
            click.echo('Your mnemonic phrase is \n{}\n'
                       'Keep it in a safe place!'.format(mnemonic_phrase))
            # TODO ks.WalletError decorator
    except ks.WalletError as error:
        click.echo(error)
    except Exception:
        click.echo('Operation aborted: unrecoverable error')


@cli.command()
@_wallet
@_address
@_index
@_password
@_indent
@click.option('-A', '--operation',
              type=str, help='Operation CREATE/TRANSFER', required=True)
@click.option('-A', '--asset', type=str, help='Asset', required=True)
@click.option('-M', '--metadata', type=str, help='Metadata', default='{}')
def prepare(wallet, address, index, password, asset, metadata, indent, operation):
    try:
        if not operation.upper() in ['CREATE', 'TRANSFER']:
            raise ks.WalletError('Operation should be either CREATE or TRANSFER')
        key = ks.get_private_key_drv(wallet, address, index, password)
        bdb = BigchainDB()
        prepared_creation_tx = bdb.transactions.prepare(
            operation=operation.upper(),
            signers=b58encode(km.privkey_to_pubkey(key.privkey)[1:]).decode(),
            asset=json.loads(asset),
            metadata=json.loads(metadata),
        )
        click.echo(
            json.dumps(prepared_creation_tx, indent=4 if indent else None)
        )
        # TODO ks.WalletError decorator
    except ks.WalletError as error:
        click.echo(error)
    except json.JSONDecodeError:
        click.echo('Operation aborted during transaction parsing')
    except Exception as err:
        click.echo('Operation aborted: unrecoverable error: {}'.format(err))


@cli.command()
@_wallet
@_address
@_index
@_password
@_transaction
def fulfill(wallet, password, address, index, transaction):
    try:
        key = ks.get_private_key_drv(wallet, address, index, password)
        tx = fulfill_transaction(
            json.loads(transaction),
            private_keys=[b58encode(key.privkey).decode()]
        )
        click.echo(json.dumps(tx))
    # TODO ks.WalletError decorator
    except ks.WalletError as error:
        click.echo(error)
    except json.JSONDecodeError:
        click.echo('Operation aborted during transaction parsing')
    except Exception:
        click.echo('Operation aborted: unrecoverable error')


@cli.command()
@_transaction
@_indent
@click.option(
    '-u', '--url',
    help='BigchaiDB url',
    type=str,
    required=True)
def commit(transaction, url, indent):
    try:
        bdb = BigchainDB(url)
        tx = bdb.transactions.send_commit(transaction)
        click.echo(
            json.dumps(tx, indent=4 if indent else None)
        )
        cache_location = '{}/{}'.format(ks.get_home_path_and_warn(),
                                        '.bdbw_cache')
        db = pickledb.load(cache_location, False)
        db.set(tx['id'], tx)
        db.dump()
    except Exception:
        click.echo('Operation aborted: unrecoverable error')
