# Validation record

Date: October 30, 2026.

## This standalone client

- Nine offline tests passed with Python 3.12, without payment dependencies installed.
- Tests cover payment-pin changes (including mainnet, token, recipient and amount), signing domain/resource mismatch, invalid headers, multiple payment options, domain normalization, redirect rejection, private key-file permissions/symlinks, exact transfer verification and read-only execution without key access or importing a payment SDK.
- Live read-only check succeeded for `example.org` at the public HTTPS endpoint. The x402 challenge matched Base Sepolia, exact test USDC amount and expected recipient. No wallet, RPC, signature or payment was used.
- CLI help checked.
- `--pay` in this refactored standalone client has not been exercised end to end. The paid path uses the operator client's tested signing and receipt-verification approach; offline tests are not a substitute for an end-to-end payment test.
- No uptime guarantee or independent security audit is claimed.

## Prior operator-client evidence

The earlier operator client completed a separate public payment and replay check:

- HTTP 200 diagnostic.
- Exactly 0.01 test USDC transferred on Base Sepolia.
- Receipt and Transfer event checked against buyer, token, recipient and amount.
- Reused authorization rejected with HTTP 402.
- Transaction: `0x6bab47df5209348ae7a9d3b164f0900baf612e2702b00852f34e0a9237aa4de2`.

No mainnet transaction or real revenue is represented by these tests.
