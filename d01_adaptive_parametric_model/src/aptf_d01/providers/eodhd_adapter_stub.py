"""EODHD adapter stub.

This placeholder intentionally performs no network activity.
Future mapping is expected to convert provider payloads into the
NormalizedObservation contract used by D01.

Expected mapping targets include:
- timestamp -> exchange_timestamp
- last/close -> price
- volume -> volume
- bid/ask -> bid/ask
- bid_size/ask_size -> bid_size/ask_size

Hard constraints in v0.1:
- no API key handling
- no HTTP calls
- no WebSocket calls
"""
