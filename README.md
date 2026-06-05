# IRA · HSA · ESA Department Dashboard

This project uses synthetic data to imitate a real-world interactive analytics dashboard which I built for a wealth management department. It demonstrates high-level reporting on a financial institution's tax-advantaged accounts for use by senior staff.

## What it shows

- **Summary** — AUM by account type (IRA, HSA, ESA), account counts, IRA Traditional/Roth split
- **Flows** — Monthly and annual contributions vs. distributions, filterable by account type
- **Lifecycle** — Account opens and closes over time, cumulative active account trend
- **RMD** — Required Minimum Distribution compliance tracking for Traditional IRA holders age 73+
- **Signing** — Electronic vs. manual document signing adoption rate by branch

## Stack

- Vanilla HTML/CSS/JS — no build step, no framework [original dashboard built in Microsoft PowerBI]
- [Chart.js 4](https://www.chartjs.org/) for all visualizations
- Python (`generate_data.py`) for synthetic data generation

## Running locally

Just open `index.html` in a browser — no server required. All data is embedded directly in the HTML.

To regenerate the synthetic dataset:
 
```bash
python3 generate_data.py
```

This outputs `ira_data.json` with 1,000 accounts, ~10,000 transactions, and pre-aggregated monthly and branch-level summaries.

## Data model

| Table | Key fields |
|-------|-----------|
| `accounts` | id, type (IRA/HSA/ESA), subtype (Traditional/Roth), branch, open_date, close_date, age, balance, signing_method |
| `transactions` | tx_id, account_id, type, amount, date |
| `monthly` | ym, atype, contributions, distributions |
| `branch_signing` | branch, electronic, manual, elec_pct |
| `opens_closes` | ym, opens, closes |

## Notes

All data was synthetically generated for portfolio demonstration purposes. No real account holder information is used.
