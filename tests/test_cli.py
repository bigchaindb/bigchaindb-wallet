"""CLI Tests"""
import pytest
import json
import random
from schema import Schema
from bigchaindb_driver import BigchainDB
from bigchaindb_wallet import _cli as cli
from bigchaindb_wallet.keystore import bdbw_derive_account, get_private_key_drv
from bigchaindb_wallet.keymanagement import ExtendedKey
import hypothesis.strategies as st
from hypothesis import given, example, settings


@pytest.mark.parametrize(
    "account,index",
    [(0, 0), (1, 1), (10, 10), (123, 123), (999, 999), (1, 4849),
     (4849, 1), (0x8000000, 0x8000000), (0xfffffff, 0xfffffff)])
def test__get_private_key_drv(
        session_wallet,
        default_password,
        keymanagement_test_vectors,
        account,
        index
):
    # TODO test raises
    key_drv = get_private_key_drv('default', account, index, default_password)
    test_xkey = ExtendedKey(keymanagement_test_vectors.privkey,
                            keymanagement_test_vectors.chaincode)
    assert key_drv == bdbw_derive_account(test_xkey, account, index)


def test_cli_init_default(tmp_home, click_runner):
    """This test runs init_key_store with no arguments.  Expected behaviour
    would be to create keystore file according to default keystore config.
    """
    result = click_runner.invoke(cli.init, ["--password", "1234"])
    conf_location = (tmp_home / '.bigchaindb_wallet')
    assert conf_location.exists()
    with open(conf_location) as conf_file:
        conf_dict = json.load(conf_file)
        assert Schema({
            'default': {  # the default account
                'chain_code': str,
                'master_pubkey': str,
                'master_privkey': {
                    'format': 'cryptsalsa208sha256base58',
                    'salt': str,
                    'key': str   # encrypted base58 encoded extended private key
                },
            }
        }).validate(conf_dict)
    assert result.exit_code == 0
    assert result.output.startswith(
        'Keystore initialized in {}\n'
        'Your mnemonic phrase is \n'
        .format(conf_location))


def test_cli_prepare(
        click_runner,
        session_wallet,
        default_password,
        prepared_hello_world_tx,
):
    result = click_runner.invoke(
        cli.prepare,
        [
            "--wallet", "default",
            "--address", "3",
            "--index", "3",
            "--operation", "cReAte",
            "--password", default_password,
            "--asset", '{"data":{"hello":"world"}}',
            '--metadata', '{"meta":"someta"}'
        ]
    )
    assert json.loads(result.output) == prepared_hello_world_tx


def test_cli_fulfill(
        click_runner,
        session_wallet,
        default_password,
        prepared_hello_world_tx,
        fulfilled_hello_world_tx
):
    result = click_runner.invoke(
        cli.fulfill,
        [
            "--wallet", "default",
            "--address", "3",
            "--index", "3",
            "--password", default_password,
            "--transaction", json.dumps(prepared_hello_world_tx)
        ]
    )
    assert json.loads(result.output) == fulfilled_hello_world_tx


def test_cli_commit(random_fulfilled_tx_gen, bdb_test_url, click_runner):
    bdb = BigchainDB(bdb_test_url)
    ftx = random_fulfilled_tx_gen(bdb)
    result = click_runner.invoke(
        cli.commit, ["--transaction", json.dumps(ftx), "--url", bdb_test_url]
    )
    assert json.loads(result.output) == ftx
