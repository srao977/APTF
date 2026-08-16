# D01 DMO/FMO Schema v0.1

DMO fields include identity/versioning, intervals, input snapshots,
Adaptive Signal snapshot, current state fan-out, half-lives,
perturbation state, volume state, parameter summary, and health metadata.

FMO fields include forward interval, directional support,
expected magnitude/persistence/decay, reversal tendency, uncertainty,
favorable/adverse excursion estimates, confidence, and metadata.

All fields are emitted as machine-readable JSONL and summarized in CSV files.
