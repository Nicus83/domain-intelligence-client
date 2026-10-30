import argparse
import asyncio
import base64
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import client


def challenge():
    return {'x402Version': 2, 'resource': {'url': client.resource_url('example.com')},
            'accepts': [{'scheme': 'exact', 'network': client.NETWORK, 'asset': client.TOKEN,
                         'payTo': client.RECIPIENT, 'amount': '10000', 'extra': {'name': 'USDC', 'version': '2'}}]}


class ClientTests(unittest.TestCase):
    def test_domain_normalization_and_url(self):
        self.assertEqual(client.normalize_domain('BÜCHER.de.'), 'xn--bcher-kva.de')
        self.assertEqual(client.resource_url('EXAMPLE.COM.'), 'https://api.x4-02.fr/v1/domain/check?domain=example.com')
        for value in ['127.0.0.1', 'http://example.com', 'x..com', 'local', 'x.local', '-x.com', 'example.com?x=1']:
            with self.subTest(value=value), self.assertRaises(client.ClientError):
                client.normalize_domain(value)

    def test_valid_challenge(self):
        data = challenge()
        headers = {'PAYMENT-REQUIRED': base64.b64encode(json.dumps(data).encode()).decode()}
        self.assertEqual(client.read_challenge(headers, client.resource_url('example.com')), data)

    def test_unsafe_payment_changes_are_rejected(self):
        for key, value in [('network', 'eip155:8453'), ('scheme', 'upto'), ('asset', '0x' + '0' * 40),
                           ('payTo', '0x' + '0' * 40), ('amount', '10001'), ('amount', '1e4')]:
            data = challenge(); data['accepts'][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(client.ClientError):
                client.validate_challenge(data, client.resource_url('example.com'))

    def test_wrong_resource_and_signing_domain_rejected(self):
        data = challenge(); data['resource']['url'] = 'http://api.x4-02.fr/v1/domain/check?domain=example.com'
        with self.assertRaises(client.ClientError): client.validate_challenge(data, client.resource_url('example.com'))
        data = challenge(); data['accepts'][0]['extra']['version'] = '3'
        with self.assertRaises(client.ClientError): client.validate_challenge(data, client.resource_url('example.com'))

    def test_bad_headers_and_multiple_payment_options_rejected(self):
        for headers in [{}, {'PAYMENT-REQUIRED': 'not-base64'}, {'PAYMENT-REQUIRED': base64.b64encode(b'[]').decode()}]:
            with self.assertRaises(client.ClientError): client.read_challenge(headers, client.resource_url('example.com'))
        data = challenge(); data['accepts'].append(copy.deepcopy(data['accepts'][0]))
        with self.assertRaises(client.ClientError): client.validate_challenge(data, client.resource_url('example.com'))

    def test_read_only_never_reads_key_or_loads_payment_sdk(self):
        headers = {'PAYMENT-REQUIRED': base64.b64encode(json.dumps(challenge()).encode()).decode()}
        real_import = __import__
        def guarded_import(name, *args, **kwargs):
            if name.split('.')[0] in ('web3', 'x402', 'eth_account'):
                raise AssertionError('Payment SDK imported during read-only check')
            return real_import(name, *args, **kwargs)
        with patch.object(client, 'request', return_value=(402, headers, b'{}')) as request, \
                patch.object(client, 'read_key', side_effect=AssertionError('Key read')), \
                patch('builtins.__import__', side_effect=guarded_import), patch('sys.stdout', new=io.StringIO()):
            asyncio.run(client.run(argparse.Namespace(domain='example.com', pay=False, key_file=None)))
        request.assert_called_once_with(client.resource_url('example.com'))

    def test_redirect_is_refused(self):
        with self.assertRaises(client.ClientError):
            client.NoRedirect().redirect_request(None, None, 302, 'redirect', {}, 'https://other.example/')

    def test_key_file_permissions_and_symlinks_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'dummy.key'
            p.write_text('not-a-real-key')
            p.chmod(0o644)
            with self.assertRaises(client.ClientError): client.read_key(p)
            link = Path(directory) / 'link.key'; link.symlink_to(p)
            with self.assertRaises(OSError): client.read_key(link)

    def test_transfer_requires_exact_recipient_and_amount(self):
        buyer = '0x' + '1' * 40
        class FakeWeb3:
            @staticmethod
            def keccak(text): return b'transfer-topic'
        log = {'address': client.TOKEN, 'topics': [b'transfer-topic', bytes.fromhex('00' * 12 + buyer[2:]),
               bytes.fromhex('00' * 12 + client.RECIPIENT[2:])], 'data': client.AMOUNT.to_bytes(32, 'big')}
        receipt = {'status': 1, 'logs': [log]}
        client.verify_transfer(receipt, buyer, FakeWeb3)
        for change in ['amount', 'recipient', 'failed']:
            bad = copy.deepcopy(receipt)
            if change == 'amount': bad['logs'][0]['data'] = (client.AMOUNT + 1).to_bytes(32, 'big')
            if change == 'recipient': bad['logs'][0]['topics'][2] = bytes(32)
            if change == 'failed': bad['status'] = 0
            with self.subTest(change=change), self.assertRaises(client.ClientError):
                client.verify_transfer(bad, buyer, FakeWeb3)


if __name__ == '__main__':
    unittest.main()
