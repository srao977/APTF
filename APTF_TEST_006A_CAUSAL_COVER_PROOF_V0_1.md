# Test 006A Causal Cover Proof V0.1

The development stream exposes only `next_observation()`. It owns the CSV iterator and never exposes a dataframe, row list, seek, index lookup, or future statistic. It skips to fixed physical row 115 without parsing reserve rows, yields through row 1114 only, checks every yielded timestamp is before `2023-03-30T08:00:00Z`, then terminates.

The Emitter receives a copied current observation, a tuple of exactly 15 immutable completed records, and copied prior state. During decision n, context IDs must equal n-15 through n-1. The current observation is appended only after immutable emission persistence. The harness requests n+1 only after state n is persisted. Audit fields record visible maximum index, future access count, context roll, and state fingerprints.

Reserve observations are inaccessible by construction. Reserve values, timestamps, OHLCV, C/Q values, labels, and statistics remain unobserved.