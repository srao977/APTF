# Test 006B Causal Cover Proof V0.1

The reserve stream owns the CSV file handle and iterator. It skips exactly the development row count using raw line advancement, then exposes only `next_observation()`. It never exposes a dataframe, list, seek, indexing API, aggregate, or future row to the frozen Emitter.

The Emitter receives one copied current row, an immutable prior-15 context maintained internally, and inherited recursive state. It commits the immutable emission and n+1 feedback state before the harness requests the next row. Current O_n is absent from W_n and enters W_(n+1) only after completion.

Append-only evidence sinks implement only `append` and `len`; they cannot be read by decision logic and do not alter the frozen rules. The primary CSV is written as a projection after each immutable emission is returned and is never read by the Emitter. The reserve stream hard-stops after 101,221 rows and does not request another source row.