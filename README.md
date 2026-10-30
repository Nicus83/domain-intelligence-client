# Domain Intelligence — x402 Python client

Check a domain's DNS records and SPF/DMARC presence through a JSON API. No API key. One x402 authorization per paid analysis.

**Public prototype · Base Sepolia only · 0.01 TEST USDC per analysis.**

[Website](https://x4-02.fr) · [API docs](https://api.x4-02.fr/docs) · [OpenAPI](https://api.x4-02.fr/openapi.json) · [Machine-readable guide](https://x4-02.fr/llms.txt)

## First request: no wallet, no dependencies, no payment

Requires Python 3.10+ on Linux or macOS; this release is tested on Linux/Python 3.12. After downloading or cloning this repository:

```sh
python3 client.py
# Check another public domain:
python3 client.py --domain example.org
```

Expected output:

```text
Challenge validated: HTTPS, Base Sepolia, exact, 0.01 test USDC, expected recipient.
Read-only check complete. No wallet, key, RPC or payment needed.
```

This verifies the live payment challenge, not a paid diagnostic. The API returns HTTP 402 until you supply an accepted payment authorization.

## Get a diagnostic with test USDC

1. Create a **dedicated test wallet**. Do not use a wallet holding real assets.
2. Get test USDC on **Base Sepolia** at the [Circle faucet](https://faucet.circle.com/). Select USDC and Base Sepolia, and enter the test buyer's public address.
3. Install the payment dependencies and run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python client.py --domain example.com --pay
```

The client asks for the test wallet's private key in your terminal without displaying or saving it. Never paste a private key into the website, an issue, or a chat.

Before signing, the client checks the live HTTPS resource URL, x402 v2, exact payment scheme, Base Sepolia network, USDC signing domain, token contract, recipient and exact amount. It checks the RPC chain and test USDC balance. It submits one payment authorization, verifies the on-chain transfer, prints the diagnostic, and reuses the same authorization once to verify rejection. **The replay test does not sign a second payment.** Redirects are refused.

If a request fails after submission, **do not retry blindly**. A payment may have settled even if you did not receive the response. Inspect the wallet, transaction and service logs first. The client never retries a payment automatically.

### For automated clients

The read-only mode is noninteractive and returns exit code 0 on success, 1 on failure, or 2 for invalid CLI arguments. To authorize a test payment from automation, use a private key file:

```sh
# Create this file securely outside the repository; contents: one test private key.
chmod 600 /secure/path/test-wallet.key
python client.py --domain example.com --pay --key-file /secure/path/test-wallet.key
```

The file must be a regular file owned by the current user, with no group/other permissions; symlinks are refused. This option targets Linux/macOS. The user or agent operator must explicitly authorize the test payment. Do not put keys in command arguments, version control or logs.

For direct SDK integration, use the live [OpenAPI schema](https://api.x4-02.fr/openapi.json) and [service manifest](https://x4-02.fr/service.json). No browser CORS integration is provided or claimed.

## Payment configuration

| Field | Pinned value |
| --- | --- |
| Protocol | x402 v2, `exact` |
| Network | Base Sepolia, `eip155:84532` |
| Token | Test USDC, `0x036CbD53842c5426634e7929541eC2318f3dCF7e` |
| Amount | `10000` atomic units = `0.01` test USDC |
| Recipient | `0x68e1f3659A7DaeA2fee5FEf1f53C50cf013f6A56` |

These values describe a test deployment. They do not represent real revenue or an offer to accept real assets.

## What the API checks

- Public DNS: A, AAAA, MX, NS, CAA and TXT.
- SPF and DMARC presence: present, absent, multiple or unknown.
- DNS errors separately from missing records.
- Normalized domain, timestamp, TTLs where available and cache indicator.

It does **not** fully validate SPF/DMARC policy, measure deliverability, inspect TLS or assess reputation/overall security. DMARC is checked at the exact domain without organizational-domain fallback.

Complete responses may be cached for up to 60 seconds, bounded by the lowest positive TTL. Cached calls still require payment. Quotas are per public IP: 60 requests/minute before payment, 30/minute after x402 validation; 16 active requests and 8 concurrent analyses maximum. Clients sharing a public IP share quotas. Limits are in memory and reset when the service restarts.

## Quick troubleshooting

| Result | Next step |
| --- | --- |
| HTTP 402 without `--pay` | Expected; the client validates this challenge. |
| HTTP 403 | Check Cloudflare blocking; use a descriptive User-Agent. This client sends one. |
| HTTP 429 | Wait for the IP rate-limit window; clients on the same public IP share a quota. |
| HTTP 503 | Service busy or DNS unavailable; do not automatically resubmit a payment. |
| Insufficient test USDC | Confirm the buyer has USDC on Base Sepolia, not on another network. |
| Network error after submission | Check settlement before considering another payment. |

## Verification and limitations

Run offline checks without installing payment dependencies:

```sh
python3 -m unittest discover -s tests -v
```

The original operator client completed an end-to-end public test on October 30, 2026: paid HTTP 200, exact on-chain transfer verified, replay rejected with HTTP 402. [Public test transaction](https://sepolia.basescan.org/tx/0x6bab47df5209348ae7a9d3b164f0900baf612e2702b00852f34e0a9237aa4de2).

This standalone client is derived from that workflow. See [VALIDATION.md](VALIDATION.md) for checks actually performed on this version. This prototype has no uptime SLA and has not had an independent security audit.

## Feedback

Try an integration and report what you built, whether the response was useful, and what was missing. Include Python version and the final HTTP status, but never a key, signed payment header or secret. Once this repository is hosted on GitHub, use its Issues tab.

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under the [MIT License](LICENSE).
