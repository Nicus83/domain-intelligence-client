#!/usr/bin/env python3
"""Domain Intelligence x402 client. Read-only by default; testnet only."""
import argparse
import asyncio
import base64
import getpass
import json
import os
from pathlib import Path
import stat
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

API = 'https://api.x4-02.fr'
NETWORK = 'eip155:84532'
RECIPIENT = '0x68e1f3659A7DaeA2fee5FEf1f53C50cf013f6A56'
TOKEN = '0x036CbD53842c5426634e7929541eC2318f3dCF7e'
AMOUNT = 10000
MAX_RESPONSE = 2 * 1024 * 1024


class ClientError(Exception):
    """Safe user-facing error; never includes key material or signed headers."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ClientError('Redirect refused. No request was forwarded to another URL.')


def normalize_domain(value):
    try:
        value = value.strip().rstrip('.').encode('idna').decode('ascii').lower()
    except UnicodeError:
        raise ClientError('Invalid domain name.') from None
    import ipaddress
    import re
    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        raise ClientError('Use a public domain, not an IP address.')
    if (len(value) > 253 or '.' not in value
            or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', part) for part in value.split('.'))
            or value.endswith(('.local', '.internal', '.localhost', '.home.arpa', '.invalid', '.test'))):
        raise ClientError('Use a valid public domain name.')
    return value


def resource_url(domain):
    return API + '/v1/domain/check?' + urlencode({'domain': normalize_domain(domain)})


def request(url, payment_headers=None):
    headers = {'User-Agent': 'DomainIntelligence-Client/0.1', 'Accept': 'application/json'}
    headers.update(payment_headers or {})
    req = Request(url, headers=headers)
    try:
        response = build_opener(NoRedirect()).open(req, timeout=90)
    except HTTPError as exc:
        response = exc
    with response:
        body = response.read(MAX_RESPONSE + 1)
        if len(body) > MAX_RESPONSE:
            raise ClientError('Response exceeds the client size limit.')
        return response.status, response.headers, body


def validate_challenge(challenge, url):
    if not isinstance(challenge, dict) or challenge.get('x402Version') != 2:
        raise ClientError('Expected an x402 v2 challenge.')
    resource = challenge.get('resource')
    if not isinstance(resource, dict) or resource.get('url') != url:
        raise ClientError('Challenge resource URL does not match the requested HTTPS URL.')
    options = challenge.get('accepts')
    if not isinstance(options, list) or len(options) != 1 or not isinstance(options[0], dict):
        raise ClientError('Expected exactly one payment option.')
    option = options[0]
    if (option.get('network') != NETWORK or option.get('scheme') != 'exact'
            or str(option.get('asset', '')).lower() != TOKEN.lower()
            or str(option.get('payTo', '')).lower() != RECIPIENT.lower()
            or str(option.get('amount')) != str(AMOUNT)):
        raise ClientError('Payment network, scheme, token, recipient or amount is not the pinned testnet configuration.')
    extra = option.get('extra')
    if not isinstance(extra, dict) or extra.get('name') != 'USDC' or extra.get('version') != '2':
        raise ClientError('Unexpected USDC signing domain.')


def read_challenge(headers, url):
    try:
        encoded = headers.get('PAYMENT-REQUIRED')
        if not encoded or len(encoded) > 65536:
            raise ValueError
        challenge = json.loads(base64.b64decode(encoded, validate=True))
    except (ValueError, TypeError):
        raise ClientError('Missing or invalid PAYMENT-REQUIRED header.') from None
    validate_challenge(challenge, url)
    return challenge


def read_key(path):
    if path:
        # Open the file without following symlinks and inspect the opened inode.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd) as stream:
            metadata = os.fstat(stream.fileno())
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid()
                    or stat.S_IMODE(metadata.st_mode) & 0o077):
                raise ClientError('Key file must be a private regular file owned by the current user (mode 600).')
            key = stream.read(256).strip()
    else:
        if not sys.stdin.isatty():
            raise ClientError('Use an interactive terminal or --key-file with a private test key file.')
        key = getpass.getpass('Dedicated TESTNET wallet private key (hidden, never saved): ').strip()
    from eth_account import Account
    try:
        return Account.from_key(key)
    except Exception:
        raise ClientError('Invalid private key. Key value omitted.') from None


def verify_transfer(receipt, buyer, web3):
    if receipt['status'] != 1:
        raise ClientError('On-chain transaction failed.')
    topic = web3.keccak(text='Transfer(address,address,uint256)')
    found = any(log['address'].lower() == TOKEN.lower() and len(log['topics']) == 3
                and log['topics'][0] == topic
                and log['topics'][1].hex()[-40:].lower() == buyer[2:].lower()
                and log['topics'][2].hex()[-40:].lower() == RECIPIENT[2:].lower()
                and int.from_bytes(log['data'], 'big') == AMOUNT for log in receipt['logs'])
    if not found:
        raise ClientError('Expected exact USDC transfer was not found in the receipt.')


async def run(args):
    domain = normalize_domain(args.domain)
    url = resource_url(domain)
    status, headers, body = request(url)
    if status != 402:
        raise ClientError(f'Expected HTTP 402, received {status}. No payment signed.')
    read_challenge(headers, url)
    print('Challenge validated: HTTPS, Base Sepolia, exact, 0.01 test USDC, expected recipient.')
    if not args.pay:
        print('Read-only check complete. No wallet, key, RPC or payment needed.')
        return

    try:
        from web3 import Web3
        from x402 import x402Client
        from x402.http import x402HTTPClient
        from x402.mechanisms.evm import EthAccountSigner
        from x402.mechanisms.evm.exact import ExactEvmClientScheme
    except ImportError:
        raise ClientError('Install requirements.txt before using --pay.') from None
    web3 = Web3(Web3.HTTPProvider('https://sepolia.base.org', request_kwargs={'timeout': 20}))
    if web3.eth.chain_id != 84532:
        raise ClientError('RPC is not Base Sepolia.')
    account = read_key(args.key_file)
    print('Test buyer:', account.address)
    abi = [{'type': 'function', 'name': 'balanceOf', 'stateMutability': 'view',
            'inputs': [{'name': 'account', 'type': 'address'}],
            'outputs': [{'name': '', 'type': 'uint256'}]}]
    contract = web3.eth.contract(address=Web3.to_checksum_address(TOKEN), abi=abi)
    if contract.functions.balanceOf(account.address).call() < AMOUNT:
        raise ClientError('Insufficient test USDC. Fund this buyer on Base Sepolia at faucet.circle.com.')
    client = x402Client()
    client.register(NETWORK, ExactEvmClientScheme(EthAccountSigner(account)))
    http = x402HTTPClient(client)
    challenge = http.get_payment_required_response(headers.get, json.loads(body))
    proof = http.encode_payment_signature_header(await http.create_payment_payload(challenge))
    print('Submitting one payment authorization. Do not retry automatically after this point.')
    status, paid_headers, paid_body = request(url, proof)
    if status != 200:
        raise ClientError(f'Paid request returned HTTP {status}. Check the wallet and settlement before retrying.')
    diagnostic = json.loads(paid_body)
    if diagnostic.get('domain') != domain or 'checked_at' not in diagnostic:
        raise ClientError('Unexpected diagnostic response after payment. Do not retry automatically.')
    settlement = http.get_payment_settle_response(paid_headers.get)
    if not settlement.success or settlement.network != NETWORK:
        raise ClientError('Settlement not confirmed on Base Sepolia. Do not retry automatically.')
    tx = settlement.transaction
    print('Settlement transaction:', tx)
    receipt = web3.eth.wait_for_transaction_receipt(tx, timeout=90)
    verify_transfer(receipt, account.address, web3)
    print('Diagnostic:')
    print(json.dumps(diagnostic, indent=2))
    replay, _, _ = request(url, proof)
    if replay != 402:
        raise ClientError(f'Replay check expected HTTP 402, received {replay}. No new authorization was created.')
    print('PASS: diagnostic HTTP 200, exact on-chain transfer verified, replay HTTP 402.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domain', default='example.com', help='Public domain to check (default: example.com)')
    parser.add_argument('--pay', action='store_true', help='Authorize one 0.01 TEST USDC payment')
    parser.add_argument('--key-file', type=Path, help='Optional private test-key file for noninteractive --pay; Linux/macOS')
    args = parser.parse_args()
    if args.key_file and not args.pay:
        parser.error('--key-file requires --pay')
    try:
        asyncio.run(run(args))
    except ClientError as exc:
        print('FAILED:', exc, file=sys.stderr)
        return 1
    except (URLError, TimeoutError):
        print('FAILED: network request failed. If payment submission started, check settlement before retrying.', file=sys.stderr)
        return 1
    except Exception as exc:
        # Third-party exceptions can contain sensitive values; print the type only.
        print(f'FAILED ({type(exc).__name__}). No automatic retry; inspect settlement before another payment.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
