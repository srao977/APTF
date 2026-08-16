# SPY Dataset Inspection v0.1

## 1. Source discovered
- Source discovered as file.

## 2. Raw path
- c:\Users\chino\APTF\data\market\raw\SPY_1min_firstratedata.csv

## 3. File format
- CSV

## 4. File size
- 11448549 bytes

## 5. SHA256
- B8688041F151AA291FC297205DC57539A4B2430B78FEA277566A0238EEE037CB

## 6. Row count
- 207824

## 7. Schema
- Columns: timestamp, open, high, low, close, volume

## 8. Timestamp format
- Parsed format: YYYY-MM-DD HH:MM:SS (timezone-naive in source)

## 9. Earliest date
- 2022-09-30 04:00:00

## 10. Latest date
- 2023-09-29 19:48:00

## 11. Raw chronology
- ASCENDING

## 12. Timezone finding
- SOURCE_TIMEZONE_EXPLICIT = NO
- Normalization assumption: America/New_York

## 13. Session coverage
- Premarket: 65846
- Regular: 97744
- Afterhours: 44234
- Unknown: 0

## 14. OHLCV profile
- See diagnostics/feature_profile.csv

## 15. Duplicates
- Duplicate timestamps: 0
- Conflicting duplicates: 0

## 16. Gaps
- See diagnostics/missing_interval_summary.csv

## 17. Anomalies
- Timestamp anomalies: 0
- OHLC anomalies: 0
- Volume anomalies: 0

## 18. Source limitations
- No explicit timezone token in source.
- No bid/ask/bid_size/ask_size/trade_size fields.

## 19. Normalized output created
- normalized/SPY_1min_normalized_v0_1.csv

## 20. Recommendation
- D01 HISTORICAL REPLAY DATA: READY WITH LIMITATIONS
