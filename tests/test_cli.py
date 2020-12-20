"""CLI Tests"""
import pytest
import json
from schema import Schema
from bigchaindb_wallet import _cli as cli


def test__get_private_key_drv_bdb_master(session_wallet,
                                         default_password,
                                         bdbw_master_xkey):
    # TODO test raises
    # TODO teset bdb keys
    key_drv = cli._get_private_key_drv('default', 0, 0, default_password)
    assert key_drv._xkey.get_master_xpriv() == bdbw_master_xkey.privkey


def test__get_public_key_drv(session_wallet,
                             default_password,
                             bdbw_master_xkey):
    # TODO test raises
    # TODO teset bdb keys
    key_drv = cli._get_public_key_drv('default', 0, 0, default_password)
    assert key_drv._xkey.get_master_xpub() == bdbw_master_xkey.pubkey


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


@pytest.mark.skip
def test_cli_create(click_runner, session_wallet, default_password, fulfilled_hello_world_tx):
    result = [click_runner.invoke(
        cli.create,
        ["--name", "default",
         "--address", "3",
         "--index", "3",
         "--password", default_password,
         "--asset", '{"data":{"hello":"world"}}',
         '--metadata', '{"meta":"someta"}']
    ) for i in range(3)]
    assert json.loads(result.output) == fulfilled_hello_world_tx
