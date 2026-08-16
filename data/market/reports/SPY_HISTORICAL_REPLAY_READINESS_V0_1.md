# SPY Historical Replay Readiness v0.1

## AVAILABLE FROM SOURCE
- timestamp
- open
- high
- low
- close
- volume

## NOT AVAILABLE FROM SOURCE
- bid
- ask
- bid_size
- ask_size
- trade_size

## DERIVED DURING NORMALIZATION
- close_return_1m (backward-looking)
- high_low_range
- high_low_range_fraction
- open_close_change
- open_close_return
- session_type
- is_regular_session
- minute_of_session

## DERIVED INSIDE D01
- relative volume
- volume density
- velocity
- acceleration
- adaptive half-life
- perturbation
- strength
- DMO
- FMO

## Questions
1. Is source readable? YES
2. Is chronology trustworthy? YES (ASCENDING)
3. Is timezone interpretable? YES (assumed America/New_York; source explicit=NO)
4. Is OHLC internally consistent? YES
5. Is volume usable? YES
6. Are irregular intervals preserved? YES
7. Can D01 calculate dt safely? YES
8. Are required D01 fields available? PASS WITH MAPPING
9. Which fields are missing? bid, ask, bid_size, ask_size, trade_size
10. Does CSVReplayProvider need mapping adjustment? YES (timestamp/price column mapping)
11. Suitable for initial D01 replay? READY WITH LIMITATIONS

## Final classification
D01 HISTORICAL REPLAY DATA: READY WITH LIMITATIONS

## Initial 6-month slice recommendation
- 2023-03-29 to 2023-09-29

## Future chronological split proposal
- 60% adaptation / 20% validation / 20% evaluation (proposal only)
