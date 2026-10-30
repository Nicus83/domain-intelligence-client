# Bazaar readiness — research, not a listing

Reviewed October 30, 2026.

The public website and its `/llms.txt` and `/service.json` files do not register the API with a facilitator catalog.

The official Bazaar extension declares the endpoint's method, query input and output schema inside the x402 `extensions.bazaar` object. Compatible facilitators can catalog those declarations. Catalog visibility is facilitator-specific; successful settlement alone does not prove indexing.

## Current deployment

- Public endpoint: `GET https://api.x4-02.fr/v1/domain/check?domain=example.com`.
- Payment: x402 v2, Base Sepolia only, exact 0.01 test USDC.
- Current facilitator: `https://x402.org/facilitator`.
- No live Bazaar extension, catalog registration or CDP credentials have been configured by this client-repository task.

## Next implementation steps

1. Inspect Bazaar support in the deployed, pinned Python SDK (2.26.0); use its actual signatures rather than assuming current main-branch examples match the installed version.
2. Declare GET query input with a public-domain example and an output schema/example explicitly labeled for diagnostics.
3. Confirm whether the existing testnet facilitator catalogs Bazaar declarations and exposes discovery. Do not assume the CDP catalog aggregates another facilitator.
4. If CDP hosting is needed, review its current account, authentication, network and billing requirements before changing the server.
5. Preserve testnet-only payment checks and validate all current smoke tests after any server change.
6. Following a separately authorized test payment, inspect catalog results or supported extension responses. A `processing` status is not proof of a finished listing, and absence of the response header is not proof of failure.

Suggested English service description:

> Public DNS records and SPF/DMARC presence as JSON. A, AAAA, MX, NS, CAA and TXT. Exact-domain DMARC only; no full policy validation, TLS or reputation assessment. Base Sepolia TESTNET only; 0.01 test USDC per call.

## Primary references

- Official specification: https://github.com/x402-foundation/x402/blob/main/specs/extensions/bazaar.md
- Official Python example: https://github.com/coinbase/cdp-sdk/blob/main/examples/python/x402/servers/bazaar.py
- Official guide: https://github.com/x402-foundation/x402/blob/main/docs/extensions/bazaar.mdx

These are research references, not a claim that this deployment has been indexed.
