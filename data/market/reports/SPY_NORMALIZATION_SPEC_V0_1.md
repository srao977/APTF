# SPY Normalization Spec v0.1

## Source schema
- timestamp -> type=string, nulls=0, unique=207824
- open -> type=numeric, nulls=0, unique=28394
- high -> type=numeric, nulls=0, unique=28918
- low -> type=numeric, nulls=0, unique=28219
- close -> type=numeric, nulls=0, unique=35305
- volume -> type=numeric, nulls=0, unique=100872

## Target schema
- entity_id
- event_timestamp_local
- event_timestamp_utc
- timezone
- open, high, low, close, volume
- close_return_1m
- high_low_range, high_low_range_fraction
- open_close_change, open_close_return
- session_type, is_regular_session, minute_of_session
- source_provider, source_dataset, source_row_number
- data_valid, quality_flags

## Column mapping
- timestamp -> event_timestamp_local/event_timestamp_utc
- open/high/low/close/volume -> direct numeric mapping

## Timestamp conversion
- Source parsed as timezone-naive local market time.
- Assumption: America/New_York.
- UTC conversion with zone-aware DST handling.

## Sorting
- Normalized output sorted ascending by event_timestamp_utc.

## Duplicate policy
- Exact duplicate rows at same timestamp: keep one.
- Conflicting duplicates: retain rows, flag DUPLICATE_CONFLICT in diagnostics.

## Invalid-row policy
- Keep rows when parseable; mark data_valid=false and quality_flags.

## Session classification
- PREMARKET: 04:00 <= t < 09:30
- REGULAR: 09:30 <= t < 16:00
- AFTERHOURS: 16:00 <= t <= 20:00
- UNKNOWN otherwise

## Derived fields
- close_return_1m uses current/previous observed close only (no future leakage).
- high_low_range, high_low_range_fraction, open_close_change, open_close_return.

## No-fill policy
- No interpolation, no synthetic bars, no forward fill.

## Traceability fields
- source_row_number retained.

## Hashing
- SHA256 on raw source and normalized output recorded in manifests.
