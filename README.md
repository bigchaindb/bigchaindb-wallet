# bigchaindb-wallet

Bigchaindb wallet sketch.

This is a wrapper around `bigchaindb_driver`, `bip32` and `mnemonic` libraries.

Here I made an attempt to provide encrypted on disk HD wallet that can be used
to create and sign BigchainDB transactions.

## CLI

Commands:
  init   Initialize keystore
  create Create transaction
  sign   Sign transaction

### init
Options:
  -s, --strength INTEGER        Seed strength. One of the following [128, 160,
                                192, 224, 256] default is 256

  -p, --password TEXT           Wallet master password.  Used to encrypt
                                private keys  [required]

  -e, --entropy TEXT            Entropy to use for seed generation. It must be
                                base64 encoded

  -l, --mnemonic-language TEXT  Mnemonic language. Currently supported
                                languages: [cinese-simplified, chinese-
                                traditional, english, french, italian,
                                japanese, korean, spanish]

  -o, --no-keystore             Do not create keystore file. Output result to
                                stdout

  -q, --quiet                   Only output the resulting mnemonic seed
  -L, --location TEXT           Keystore file location

### create
Options:
  -n, --name TEXT        Wallet to use
  -a, --address INTEGER  Address to use
  -i, --index INTEGER    Address index
  -p, --password TEXT    Root account password
  -A, --asset TEXT       Asset
  -M, --metadata TEXT    Metadata
  -I, --indent           Indent result

### sign
Options:
  -n, --name TEXT        Wallet to use
  -a, --address INTEGER  Address to use
  -i, --index INTEGER    Address index
  -p, --password TEXT    Root account password


## Warnings and limitations
This package is in PoC state.  It is likely to brake or not work at all.  More
tests, features and bug fixes are on the way.

### TODO shortlist
- Account discovery
- Public key derivations

  Underling library uses secp256k1 while BigchainDB is using ed25519 Because key
  size is 32 private keys can be used interchangeably. But major limitation at
  the moment you can not derive public keys from extended public keys at the
  moment.  Bip32 style Ed25519 key derivation library has to be implemented to
  have this feature.
  
