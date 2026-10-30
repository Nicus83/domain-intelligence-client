# Launch draft — not posted

Building an agent or script that needs DNS context?

I built Domain Intelligence: DNS records and SPF/DMARC presence returned as JSON, accessible through x402 without an API key.

The public prototype runs on Base Sepolia with test USDC only. A Python client validates the payment terms before signing, checks settlement, and tests replay rejection. Its default mode needs no wallet and does not pay.

I'm looking for five developers to try a real integration and tell me what's missing. Would the structured response save you work compared with making DNS queries yourself?

Website: https://x4-02.fr
API docs: https://api.x4-02.fr/docs
Client: https://x4-02.fr/client.py (current website download; GitHub link to follow after publication)

Scope: DNS and email-policy presence, not a reputation score, security audit or full SPF/DMARC validator.

# Suggested demonstration

1. Show the website and the testnet notice.
2. Run `curl https://api.x4-02.fr/health`.
3. Run `python3 client.py` to inspect the challenge without a wallet.
4. If demonstrating a separately authorized test payment, show the public buyer address and final response, never the key or signed authorization.
5. Show an actual JSON response and explain the diagnostic limitations.

# First tester feedback

- What workflow did you integrate it into?
- Did you complete the first read-only check? The first test payment?
- Was the response useful, and what was missing?
- Would you use it again? What would make it worth paying for?

No announcements or outreach have been sent. No Bazaar listing is claimed.
