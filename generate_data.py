import json, random, math
from datetime import date, timedelta

random.seed(42)

BRANCHES = ["Clearwater", "Tampa", "St. Petersburg", "Brandon", "Sarasota",
            "Lakeland", "Orlando", "Gainesville", "Fort Myers", "Naples"]

ACCOUNT_TYPES = ["IRA", "HSA", "ESA"]
IRA_SUBTYPES  = ["Traditional", "Roth"]

# signing method adoption: some branches are heavy electronic, some laggard
BRANCH_ELEC_RATE = {
    "Clearwater": 0.88, "Tampa": 0.82, "St. Petersburg": 0.79,
    "Brandon": 0.55, "Sarasota": 0.71, "Lakeland": 0.45,
    "Orlando": 0.85, "Gainesville": 0.60, "Fort Myers": 0.52, "Naples": 0.67
}

def rand_date(start, end):
    return start + timedelta(days=random.randint(0, (end-start).days))

START = date(2022, 1, 1)
END   = date(2024, 12, 31)

# ── Accounts ──────────────────────────────────────────────────────────────────
accounts = []
for i in range(1, 1001):
    atype   = random.choices(ACCOUNT_TYPES, weights=[0.60, 0.28, 0.12])[0]
    subtype = random.choice(IRA_SUBTYPES) if atype == "IRA" else None
    branch  = random.choice(BRANCHES)
    open_dt = rand_date(START - timedelta(days=365*5), END - timedelta(days=30))
    age     = random.randint(18, 85)
    # some accounts close
    closed = random.random() < 0.08
    close_dt = rand_date(open_dt + timedelta(days=90), END) if closed else None
    balance = round(random.lognormvariate(10.2, 1.1), 2)  # realistic spread
    elec    = random.random() < BRANCH_ELEC_RATE[branch]
    accounts.append({
        "id": f"ACC{i:04d}", "type": atype, "subtype": subtype,
        "branch": branch, "open_date": str(open_dt),
        "close_date": str(close_dt) if close_dt else None,
        "age": age, "balance": balance,
        "signing_method": "Electronic" if elec else "Manual"
    })

# ── Transactions ──────────────────────────────────────────────────────────────
TX_TYPES = {
    "IRA":  ["Contribution", "Distribution", "Rollover In", "Rollover Out", "RMD"],
    "HSA":  ["Contribution", "Distribution", "Employer Contribution"],
    "ESA":  ["Contribution", "Distribution", "Rollover In"],
}

transactions = []
tx_id = 1
for acc in accounts:
    atype    = acc["type"]
    open_dt  = date.fromisoformat(acc["open_date"])
    close_dt = date.fromisoformat(acc["close_date"]) if acc["close_date"] else END
    tx_start = max(open_dt, START)
    if tx_start >= close_dt: continue
    n_tx = random.randint(2, 18)
    for _ in range(n_tx):
        tx_date = rand_date(tx_start, close_dt)
        tx_type = random.choices(TX_TYPES[atype],
            weights=[0.5,0.25,0.1,0.05,0.1] if atype=="IRA" else
                    [0.5,0.35,0.15]          if atype=="HSA" else
                    [0.6,0.25,0.15])[0]
        # RMD only for age >= 73 Traditional IRA
        if tx_type == "RMD" and (acc["subtype"] != "Traditional" or acc["age"] < 73):
            tx_type = "Distribution"
        amount = round(random.uniform(250, 7000) if "Contribution" in tx_type
                       else random.uniform(500, 15000), 2)
        transactions.append({
            "tx_id": f"TX{tx_id:05d}", "account_id": acc["id"],
            "type": tx_type, "amount": amount,
            "date": str(tx_date), "year": tx_date.year, "month": tx_date.month
        })
        tx_id += 1

# ── Aggregate helpers ─────────────────────────────────────────────────────────
# monthly net flows by account type
from collections import defaultdict

monthly = defaultdict(lambda: {"contributions": 0, "distributions": 0, "count": 0})
for tx in transactions:
    key = (tx["year"], tx["month"], tx["type"].split()[0] if "Contribution" in tx["type"] else
           ("Distribution" if "Distribution" in tx["type"] or tx["type"]=="RMD" else "Other"))
    # simpler: bucket into in/out
    ym = f"{tx['year']}-{tx['month']:02d}"
    atype = next(a["type"] for a in accounts if a["id"] == tx["account_id"])
    k = (ym, atype)
    if "Contribution" in tx["type"]:
        monthly[k]["contributions"] += tx["amount"]
    elif "Distribution" in tx["type"] or tx["type"] == "RMD":
        monthly[k]["distributions"] += tx["amount"]
    monthly[k]["count"] += 1

monthly_list = [{"ym": k[0], "atype": k[1], **v} for k, v in sorted(monthly.items())]

# signing by branch
branch_signing = defaultdict(lambda: {"Electronic": 0, "Manual": 0})
for acc in accounts:
    branch_signing[acc["branch"]][acc["signing_method"]] += 1

branch_signing_list = [
    {"branch": b, "electronic": v["Electronic"], "manual": v["Manual"],
     "total": v["Electronic"]+v["Manual"],
     "elec_pct": round(v["Electronic"]/(v["Electronic"]+v["Manual"])*100, 1)}
    for b, v in sorted(branch_signing.items(), key=lambda x: -x[1]["Electronic"]/(x[1]["Electronic"]+x[1]["Manual"]))
]

# summary stats
total_accounts = len(accounts)
active_accounts = sum(1 for a in accounts if not a["close_date"])
total_balance = round(sum(a["balance"] for a in accounts if not a["close_date"]), 2)
total_contributions = round(sum(t["amount"] for t in transactions if "Contribution" in t["type"]), 2)
total_distributions = round(sum(t["amount"] for t in transactions if "Distribution" in t["type"] or t["type"]=="RMD"), 2)

by_type = {}
for atype in ACCOUNT_TYPES:
    accs = [a for a in accounts if a["type"] == atype and not a["close_date"]]
    by_type[atype] = {
        "active": len(accs),
        "balance": round(sum(a["balance"] for a in accs), 2)
    }

# account opens/closes by month
opens_closes = defaultdict(lambda: {"opens": 0, "closes": 0})
for acc in accounts:
    od = date.fromisoformat(acc["open_date"])
    if START <= od <= END:
        opens_closes[f"{od.year}-{od.month:02d}"]["opens"] += 1
    if acc["close_date"]:
        cd = date.fromisoformat(acc["close_date"])
        if START <= cd <= END:
            opens_closes[f"{cd.year}-{cd.month:02d}"]["closes"] += 1

opens_closes_list = [{"ym": k, **v} for k, v in sorted(opens_closes.items())]

# RMD eligible (Traditional IRA, age >= 73)
rmd_eligible = [a for a in accounts if a["type"]=="IRA" and a["subtype"]=="Traditional" and a["age"]>=73 and not a["close_date"]]
rmd_txs = [t for t in transactions if t["type"]=="RMD"]
rmd_account_ids = {t["account_id"] for t in rmd_txs}
rmd_compliant = sum(1 for a in rmd_eligible if a["id"] in rmd_account_ids)

output = {
    "accounts": accounts,
    "transactions": transactions,
    "monthly": monthly_list,
    "branch_signing": branch_signing_list,
    "opens_closes": opens_closes_list,
    "summary": {
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "total_balance": total_balance,
        "total_contributions": total_contributions,
        "total_distributions": total_distributions,
        "by_type": by_type,
        "rmd_eligible": len(rmd_eligible),
        "rmd_compliant": rmd_compliant,
    }
}

with open("/sessions/determined-jolly-pascal/mnt/outputs/ira_data.json", "w") as f:
    json.dump(output, f)
print("accounts:", len(accounts))
print("transactions:", len(transactions))
print("summary:", json.dumps(output["summary"], indent=2))
