# Contributing

Keep this client testnet-only and preserve explicit opt-in payment, exact payment checks, redirect refusal and no automatic payment retries.

Run `python3 -m unittest discover -s tests -v` before proposing code changes. Tests must not send payments or access external services. Real-network tests belong in a separately authorized manual session.

For bug reports, include reproduction steps, Python/OS versions and HTTP status. Do not include keys, wallet files, signed headers, account credentials or infrastructure configuration. For security concerns, avoid public disclosure of exploitable details; request a private reporting channel from the maintainer first.
