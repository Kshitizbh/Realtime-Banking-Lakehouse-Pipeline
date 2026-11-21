# Dataset

Local only, in git-ignored `data/` (156 files). Never committed.

```
data/
├── batch/
│   ├── accounts/       account_snapshot_2026-01-01.csv
│   ├── balances/       account_balances_2026-01-DD.csv   (30 days)
│   ├── customers/      customer_snapshot_2026-01-01.csv
│   ├── settlements/    settlement_2026-01-DD.csv         (30 days)
│   └── transactions/   transactions_2026-01-DD.csv       (30 days)
├── manifest/           source_manifest.csv
├── reference/          branches.csv, merchant_categories.csv, transaction_types.csv
└── streaming/          *_2026-01-DD.jsonl (transaction events + malformed events)
```

## Which door each file uses

## Profile (row counts, columns, types)

## Known data-quality traps
