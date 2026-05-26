# Rajasthan Jal Board — Full Build Prompt
## Consumer Management & Billing System v1.0
### Single Coding Agent — Complete Project

---

# TASK

Build the complete Rajasthan Jal Board Consumer Management & Billing System.
This is a two-part system:
- **Part 1:** Python Tkinter Desktop App (admin-only, runs locally)
- **Part 2:** Website on Firebase Hosting (used by meter readers in the field)

Read this entire prompt before writing a single line of code.
Follow every specification exactly. Do not add features not described here.

---

# FILE STRUCTURE (hard limits — do not exceed)

```
project/
├── Python App (max 13 .py files)
│   ├── firebase_config.py
│   ├── firebase_client.py
│   ├── utils.py
│   ├── billing_engine.py
│   ├── main.py
│   ├── consumers.py
│   ├── meter_readers.py
│   ├── charges_config.py
│   ├── billing.py
│   ├── readings.py
│   ├── payments.py
│   ├── reports.py
│   └── audit_log.py
│
├── public/ (website — max 8 HTML files + shared assets)
│   ├── index.html
│   ├── search.html
│   ├── reading.html
│   ├── confirmation.html
│   ├── correction.html
│   ├── cannot-read.html
│   ├── ledger.html
│   ├── my-readings.html
│   ├── style.css
│   ├── billing-engine.js
│   └── firebase_config.js
│
├── pdf_templates/           ← HTML templates for WeasyPrint PDF generation
│   ├── csd_sheet.html
│   ├── payment_receipt.html
│   └── consumer_ledger.html
│
├── firestore.rules
├── firebase.json
└── .firebaserc
```

Merge related logic into the same file. No splitting into many small modules.

---

# TECH STACK

**Python App:**
- `tkinter` + `ttk` for GUI
- `firebase-admin` SDK for all Firestore and Auth operations
- `openpyxl` for Excel import/export
- `weasyprint` for ALL PDF generation (CSD sheets, payment receipts, ledger exports)
- `matplotlib` with `FigureCanvasTkAgg` for embedded charts
- Font: `("Segoe UI", 10)` throughout the entire app
- All Firestore calls run in background threads to keep UI responsive

**Website:**
- Vanilla JS only — no frameworks, no jQuery
- Firebase JS SDK v9 (modular, from CDN — pick one stable version and use it across all 8 files)
- Single `style.css` — minimal, functional, government-utility style
- Mobile-first — designed for Android phones used in the field

---

# FORMATTING RULES (apply everywhere, no exceptions)

- All readings and consumption: **kiloliters (KL)**
- All currency: **Indian Rupees (₹)**, formatted as `₹1,234.56`
- All dates: **DD-MM-YYYY**
- Bill total: **ceiling** (round up to nearest rupee — `math.ceil` / `Math.ceil`)

---

# CONSUMER STATIC DATA (CSD)

| Field | Type | Notes |
|---|---|---|
| cin_no | String | Unique primary key (indexed) |
| name | String | Required |
| zone | Integer | Assigned zone number |
| contact_number | Number | |
| category | Enum | "Domestic" \| "Non-Domestic" \| "Industrial" |
| meter_size | Enum | "15mm"\|"20mm"\|"25mm"\|"40mm"\|"50mm"\|"80mm"\|"100mm"\|"150mm" |
| meter_serial_no | String | Indexed |
| initial_meter_reading | Number | KL; entered once at creation; stored as `last_reading` |
| address_longitude | Decimal | High precision |
| address_latitude | Decimal | High precision |
| address_pin_code | Number | |
| address_area_location | String | |
| address_landmark | String | |
| aadhaar_phed_no | String | |
| apl_bpl | Enum | "APL" \| "BPL" (future subsidy; does NOT affect billing) |
| custom_attributes | Map<String,String> | Admin-defined key-value pairs; shown on CSD printout only |
| consumer_status | Enum | "Active"\|"Inactive"\|"Meter Faulty"\|"Disconnected"\|"Disputed" |
| credit_balance | Number | Auto-updated on payment |
| outstanding_balance | Number | Auto-updated on bill finalization and payment |
| is_active | Boolean | |
| created_at | Timestamp | |
| updated_at | Timestamp | |

---

# FIRESTORE DATA STRUCTURE

```
consumers/{cin_no}
  All CSD fields + last_reading (KL), credit_balance, outstanding_balance,
  status, is_active, created_at, updated_at

billing_cycles/{cycle_id}
  zones: array of integers
  start_date: string (DD-MM-YYYY)
  end_date: string (DD-MM-YYYY)
  last_payment_date: string (DD-MM-YYYY)        ← calculated automatically (see Billing Cycle section)
  grace_period_months: integer (1 or 2)         ← set by admin at cycle initiation
  status: "open" | "closed"
  initiated_by: string (admin name)
  initiated_at: Timestamp
  closed_at: Timestamp | null
  consumer_count_per_zone: map {zone_int: count}

readings/{reading_id}
  cin_no, cycle_id, previous_reading (KL), current_reading (KL),
  consumption (KL), reading_date (DD-MM-YYYY), reading_time,
  reader_uid, reader_name, full_bill_breakdown (map),
  status: "finalized" | "skipped",
  edited_by_admin: bool, cannot_read_reason: string | null,
  submitted_at: Timestamp, edit_window_expiry: Timestamp,
  anomaly_flagged: bool

correction_queries/{query_id}
  reading_id, cin_no, cycle_id, reader_uid, reader_name, reader_employee_id,
  consumer_info_snapshot (map), previous_reading, submitted_reading,
  requested_corrected_reading, reason, status: "pending"|"approved"|"rejected",
  rejection_note, created_at, resolved_at

payments/{payment_id}
  cin_no, amount, payment_mode: "Cash"|"E-Mitra", emitra_key,
  payment_date (DD-MM-YYYY — source date for LPS logic),
  entry_date (DD-MM-YYYY — actual date of data entry),
  cycle_id, notes, received_by (admin name), receipt_number

meter_readers/{uid}
  uid, name, employee_id, username, phone_number,
  designation, address, zone (integer, optional — default filter, NOT access restriction),
  is_active, created_at

charges_config/current
  All tariff rates as named fields.
  Written only by Python app via Admin SDK.
  Read by website JS billing engine.

charges_config_history/{entry_id}
  snapshot_before (map), changed_by, changed_at, admin_note

custom_adjustments/{adj_id}
  cin_no, type: "penalty"|"waiver"|"lps_waiver",
  amount, reason_note (required), applied_by, applied_at, cycle_id

audit_log/{log_id}
  action_type, performed_by_uid, performed_by_name,
  target_document, old_value, new_value, timestamp

meter_replacement_log/{log_id}
  cin_no, old_meter_serial, new_meter_serial,
  replacement_date (DD-MM-YYYY), new_initial_reading (KL),
  recorded_by, recorded_at
```

**Firestore Indexes:**
- `consumers`: indexed on `cin_no`, `meter_serial_no`
- `readings`: indexed on `cin_no + submitted_at`
- `payments`: indexed on `cin_no + payment_date`

---

# BILLING CYCLE — KEY RULES

## Last Payment Date (CALCULATED — NOT manually entered)

When initiating a billing cycle, the admin sets:
1. **Billing Period Start Date**
2. **Billing Period End Date**
3. **Grace Period:** `1 month` or `2 months` (radio button / dropdown)

The `last_payment_date` is **automatically calculated** as:
```
last_payment_date = billing_period_end_date + grace_period_months
```
- "1 month" means: add exactly 1 calendar month (e.g., end date 31-03-2025 → last payment date 30-04-2025)
- "2 months" means: add exactly 2 calendar months (e.g., end date 31-03-2025 → last payment date 31-05-2025)
- Use Python's `dateutil.relativedelta` for month arithmetic; JS side use equivalent logic
- The calculated `last_payment_date` is **shown as a preview** in the form before the admin confirms
- Both `grace_period_months` (integer) and the computed `last_payment_date` are stored on the billing_cycle document

## Zone Locking

A zone already included in an **open** cycle cannot be selected for a new cycle until the current one is manually closed by admin.

## Billing Cycle Close Checklist

Before closing, show:
- Consumers with pending readings: N
- Consumers marked "Cannot Read": N
- Consumers with unresolved correction queries: N
- Total billed: ₹X | Total collected: ₹Y | Outstanding: ₹Z

Admin can close despite pending items (with confirmation dialog). On close:
- `cycle.status` → `"closed"`
- All included zones freed for new cycles
- Outstanding balances carried forward (already stored on consumer doc)
- Readings locked (admin override still possible)

---

# WEBSITE — ACTIVE CYCLE ZONE RESTRICTION

**This is a critical security and workflow rule:**

Meter readers on the website can **only look up and submit readings for consumers whose zone has an active (open) billing cycle**.

**Implementation:**

1. **On login** (`index.html` → after successful auth):
   - Fetch all `billing_cycles` where `status == "open"` from Firestore
   - Extract the flat list of all zones across all open cycles: e.g., `[1, 2, 5, 7]`
   - Store in `sessionStorage` as `"active_zones"` (JSON array of integers)

2. **On consumer search** (`search.html`):
   - After finding a consumer, check if `consumer.zone` is in `active_zones`
   - If **zone IS in active cycles**: show consumer info + "Enter Reading" button normally
   - If **zone is NOT in active cycles**: show consumer info BUT replace "Enter Reading" with a disabled grey button labelled `"No Active Cycle for Zone X"` — the meter reader can still view the ledger but cannot enter a reading

3. **On reading.html** (defense-in-depth):
   - Re-verify on page load that the consumer's zone is in `active_zones` (re-read from sessionStorage)
   - If check fails: show error message "This consumer's zone has no active billing cycle" and hide the submit form

4. **active_zones is refreshed** every time the user visits `search.html` (re-fetch open cycles on each search page load) to stay current without requiring re-login

---

# FIRESTORE SECURITY RULES

```javascript
// Meter readers (Firebase Auth users) can:
//   READ:  consumers, billing_cycles, charges_config
//   WRITE readings: only own submissions (reader_uid == auth.uid)
//          cannot edit after edit_window_expiry has passed
//   WRITE correction_queries: only own (reader_uid == auth.uid)
//   CANNOT ACCESS: payments, custom_adjustments, audit_log,
//                  charges_config (write), other readers' meter_readers docs
// Admin: uses Firebase Admin SDK — bypasses all rules by design
```

---

# BILLING ENGINE RULES (PHED Rajasthan Water Tariff 2025)

All rates stored in `charges_config/current`. Values below are the 2025 baseline (used as documentation in code comments only — always read from rates dict/object at runtime, never hardcode).

## Domestic (15mm–25mm) — Slab per KL/month
| Slab | Consumption | Rate |
|---|---|---|
| a | 0–8 KL | ₹7.00/KL |
| b | 8.001–15 KL | ₹9.00/KL |
| c | 15.001–40 KL | ₹18.00/KL |
| d | Above 40 KL | ₹22.00/KL |

Special: **No water charges** if 15mm + functional meter + consumption ≤ 15 KL.

**Domestic Minimum Monthly Charges** (only if consumption > 15 KL):
| Meter Size | Condition | Min Charge |
|---|---|---|
| 15mm | avg ≤ 8 KL | ₹88 |
| 15mm | avg > 8 KL | ₹220 |
| 20mm | — | ₹880 |
| 25mm | — | ₹2,200 |

## Flat Rate — Rural 15mm Domestic
₹110/connection/family (up to 2 taps). Fixed and sewerage charges still apply.

## Non-Domestic (15mm–25mm) — Slab per KL/month
| Slab | Consumption | Rate |
|---|---|---|
| a | 0–15 KL | ₹40.00/KL |
| b | 15.001–40 KL | ₹73.00/KL |
| c | Above 40 KL | ₹97.00/KL |

Min Monthly: 15mm ₹880 | 20mm ₹2,200 | 25mm ₹3,520

## Industrial (15mm–25mm) — Slab per KL/month
| Slab | Consumption | Rate |
|---|---|---|
| a | 0–15 KL | ₹154.00/KL |
| b | 15.001–40 KL | ₹198.00/KL |
| c | Above 40 KL | ₹220.00/KL |

Min Monthly: 15mm ₹2,200 | 20mm ₹3,960 | 25mm ₹6,160

## Bulk Connections (> 25mm)
Water rate per KL: Domestic ₹25 | Non-Domestic ₹97 | Industrial ₹220

| Size | Meter Svc Charge | Min Dom | Min Non-Dom | Min Industrial |
|---|---|---|---|---|
| 40mm | ₹220 | ₹6,600 | ₹10,560 | ₹29,900 |
| 50mm | ₹440 | ₹11,000 | ₹17,600 | ₹46,700 |
| 80mm | ₹550 | ₹26,400 | ₹44,000 | ₹1,19,400 |
| 100mm | ₹660 | ₹41,800 | ₹68,200 | ₹1,86,600 |
| 150mm | ₹770 | ₹96,600 | ₹1,85,100 | ₹4,19,700 |

Fixed Charges/month (Bulk):
| Size | Domestic | Non-Domestic | Industrial |
|---|---|---|---|
| 40mm | ₹55 | ₹110 | ₹220 |
| 50mm | ₹82.50 | ₹165 | ₹330 |
| 80mm | ₹110 | ₹220 | ₹440 |
| 100mm | ₹165 | ₹330 | ₹550 |
| 150mm | ₹220 | ₹440 | ₹660 |

## General Charges (All Categories)
- **Fixed Charge (Capital Renovation):** Domestic ₹27.50 | Non-Dom ₹55 | Industrial ₹110/month
  *(NOT applicable on flat rate rural connections)*
- **Meter Service Charge (15–25mm only):** 15mm ₹22 | 20mm ₹55 | 25mm ₹110/month

## Infrastructure Development Surcharge (IDS)
- Up to 15 KL: No IDS
- 15.001–40 KL: 25% of total monthly charges
- Above 40 KL: 35% of total monthly charges

## Late Payment Surcharge (LPS)
- Payment date ≤ `last_payment_date` → **No LPS**
- Within 2 months after `last_payment_date` → **10% of total bill**
- Beyond 2 months → **10% LPS + 18% annual interest on outstanding**
- Credit balance covering full bill → No LPS, not flagged as defaulter
- Admin can waive full or partial LPS with mandatory reason note (logged in audit trail)

## Reading Anomaly Detection
If consumption > 3× consumer's 6-month average: website flags before submission. Meter reader must confirm or cancel. Flagged readings visible to admin.

## Negative Consumption
If `current_reading < last_reading`: block submission. Meter reader must flag as meter replacement. Admin records replacement via Meter Replacement Log.

## Annual Tariff Increment
All charges × 1.10 every year from 1st April. Admin applies via one-click button in Charges Configuration (confirmation required).

## APL/BPL
Stored on consumer record for future subsidy reference. Does NOT affect current billing.

## Bill Rounding
Total bill rounded **up** to nearest rupee (`Math.ceil` / `math.ceil`).

## Bill Breakdown Map (stored on reading document)
```
water_charge, slab_details (array of {slab, kl, rate, amount}),
minimum_charge_applied (bool), minimum_charge_amount,
fixed_charge, meter_service_charge,
ids_charge, ids_rate_pct,
previous_outstanding, credit_applied, remaining_credit,
lps_amount, lps_type ("none" | "10pct" | "10pct_plus_interest"),
subtotal_before_lps, total_before_rounding, total_amount (ceiling),
is_anomaly (bool), is_flat_rate_rural (bool)
```

---

# WORKFLOW SUMMARY

1. **Consumer Static Data Management** (Python app) — Add/Edit/Deactivate/Import/Export consumers; set status flags
2. **Billing Cycle Initiation** (Python app) — Select zones, set period, set grace period (1 or 2 months); last_payment_date auto-calculated
3. **CSD Sheet Printing** (Python app, before cycle begins) — WeasyPrint PDF; each page = one consumer's CSD + last_reading + blank slots
4. **Meter Reading & Charge Calculation** (Website) — Search by CIN/meter serial; only active-cycle zones searchable for reading entry; JS billing engine calculates live
5. **Reading Correction Window** (Website) — 5-minute free edit; after: raise Correction Query; admin approves/rejects
6. **Payment In** (Python app only) — Cash or E-Mitra; payment date used for LPS logic; bulk Excel import; WeasyPrint receipt PDF
7. **Billing Cycle Close** (Python app) — Checklist shown; manual close by admin

---

# PDF GENERATION — WeasyPrint (ALL PDFs)

**Use WeasyPrint for ALL PDF generation** in the Python app.
The pattern: render an HTML template string with Python string formatting or Jinja2, then convert to PDF bytes using WeasyPrint.

```python
from weasyprint import HTML

def render_pdf(html_string: str) -> bytes:
    return HTML(string=html_string).write_pdf()
```

Save HTML templates in `pdf_templates/` folder as `.html` files.
Load them with `open("pdf_templates/csd_sheet.html").read()` and fill placeholders with Python `.format()` or a simple template substitution.

**Do NOT use reportlab anywhere in this project.**

## PDF Template: `pdf_templates/csd_sheet.html`

A single-consumer CSD printout page. Designed to print cleanly on A4.

```
Page layout:
  ┌─────────────────────────────────────────┐
  │  Rajasthan Jal Board (PHED)             │
  │  Consumer Static Data Sheet             │
  │  Zone: {zone} | Date: {date}            │
  ├─────────────────────────────────────────┤
  │  CIN No: _________ | Meter Serial: ___  │
  │  Name: ____________ | Category: _______ │
  │  Meter Size: ______ | APL/BPL: ________ │
  │  Contact: _________ | Aadhaar/PHED: ___ │
  │  Address: ________________________________│
  │  Landmark: _________ | Pin: ____________ │
  │  Lat/Long: ________________________      │
  │  Status: _________ | Is Active: ________ │
  │  Custom Attributes: (table of key-value) │
  ├─────────────────────────────────────────┤
  │  CURRENT CYCLE READING                  │
  │  Last Reading: {last_reading} KL        │
  │  ┌──────────────┬──────────────────┐    │
  │  │ Current Reading (KL) │ ________ │    │
  │  │ Consumption (KL)     │ ________ │    │
  │  ├──────────────┴──────────────────┤    │
  │  │ CHARGES BREAKDOWN               │    │
  │  │ Water Charges:       ₹ ________ │    │
  │  │ Fixed Charge:        ₹ ________ │    │
  │  │ Meter Service Chg:   ₹ ________ │    │
  │  │ IDS:                 ₹ ________ │    │
  │  │ LPS (if applicable): ₹ ________ │    │
  │  │ Previous Outstanding:₹ ________ │    │
  │  │ ─────────────────────────────── │    │
  │  │ TOTAL AMOUNT DUE:    ₹ ________ │    │
  │  └─────────────────────────────────┘    │
  │  Meter Reader Signature: ______________ │
  └─────────────────────────────────────────┘
```

Use `@page { size: A4; margin: 15mm; }` in the template's `<style>` tag.
Use `page-break-after: always` on each consumer's section when printing multiple consumers.

## PDF Template: `pdf_templates/payment_receipt.html`

A formal payment receipt. Designed to print on A5 or half-A4.

```
┌──────────────────────────────────────┐
│  RAJASTHAN JAL BOARD (PHED)         │
│  Payment Receipt                    │
│  Receipt No: {receipt_number}       │
│  Date of Receipt: {entry_date}      │
├──────────────────────────────────────┤
│  Consumer Details                   │
│  CIN No: {cin_no}                   │
│  Name: {name}                       │
│  Zone: {zone} | Category: {cat}     │
│  Address: {address}                 │
├──────────────────────────────────────┤
│  Payment Details                    │
│  Amount Paid: ₹{amount}             │
│  Payment Mode: {mode}               │
│  E-Mitra Key: {emitra_key}          │  ← shown only if E-Mitra
│  Payment Date: {payment_date}       │
│  Billing Cycle: {cycle_period}      │
│  Notes: {notes}                     │
├──────────────────────────────────────┤
│  Balance After Payment              │
│  Outstanding Balance: ₹{outstanding}│
│  Credit Balance: ₹{credit}         │
├──────────────────────────────────────┤
│  Received By: {received_by}         │
│  [Authorised Signatory]             │
│  Rajasthan Jal Board                │
└──────────────────────────────────────┘
```

## PDF Template: `pdf_templates/consumer_ledger.html`

A full consumer ledger for print/export. A4 portrait.
Sections: Consumer Info, Readings History (table), Payments History (table), Custom Adjustments, Meter Replacement History, Balance Summary.

---

# DETAILED FILE SPECIFICATIONS

---

## `firebase_config.py`

Placeholder file. Defines a constant `SERVICE_ACCOUNT_KEY_PATH = "serviceAccountKey.json"`. Exposes `get_firebase_app()` which initializes and returns the Firebase Admin app (idempotent — returns existing app on repeat calls).

---

## `firebase_client.py`

Full Firebase Admin SDK client. All Firestore/Auth wrapper functions. No threading here — threading is handled by callers via `utils.run_in_thread`.

Use `firestore.SERVER_TIMESTAMP` for timestamps on writes.
Use atomic transactions or `WriteBatch` wherever `outstanding_balance` or `credit_balance` on the consumer document is modified alongside another write.
Use `doc.update()` (not `doc.set()`) for partial updates — only changed fields.

**Implement all of the following functions with full docstrings:**

### Consumer Functions
```python
get_consumer(cin_no: str) -> dict | None
get_consumer_by_meter_serial(meter_serial_no: str) -> dict | None
create_consumer(data: dict, admin_name: str) -> str              # returns cin_no; writes audit_log
update_consumer(cin_no: str, updates: dict, admin_name: str) -> None   # writes audit_log; use update() not set()
deactivate_consumer(cin_no: str, admin_name: str) -> None
reactivate_consumer(cin_no: str, admin_name: str) -> None
bulk_create_consumers(data_list: list, admin_name: str) -> dict  # returns {success: int, errors: list}
list_consumers(filters: dict = None) -> list                     # supports zone, status, is_active
```

### Billing Cycle Functions
```python
create_billing_cycle(data: dict, admin_name: str) -> str         # returns cycle_id; data includes grace_period_months + computed last_payment_date
get_billing_cycle(cycle_id: str) -> dict | None
get_open_cycles() -> list
get_open_cycle_zones() -> list                                   # flat list of all zone ints in open cycles — used by website
close_billing_cycle(cycle_id: str, admin_name: str) -> None
list_billing_cycles(status: str = None) -> list
```

### Reading Functions
```python
get_reading(reading_id: str) -> dict | None
get_readings_for_cycle(cycle_id: str, cin_no: str = None) -> list
admin_update_reading(reading_id: str, updates: dict, admin_name: str) -> None   # sets edited_by_admin=True; writes audit_log
bulk_update_readings(updates_list: list, admin_name: str) -> dict
```

### Correction Query Functions
```python
get_pending_correction_queries() -> list
get_all_correction_queries(cycle_id: str = None) -> list
approve_correction_query(query_id: str, admin_name: str) -> None  # applies corrected reading + recalculates bill atomically
reject_correction_query(query_id: str, rejection_note: str, admin_name: str) -> None
```

### Payment Functions
```python
record_payment(data: dict, admin_name: str) -> str               # returns payment_id; updates consumer outstanding/credit atomically; writes audit_log
bulk_record_payments(data_list: list, admin_name: str) -> dict
get_payments_for_consumer(cin_no: str, cycle_id: str = None) -> list
list_payments(filters: dict = None) -> list                      # supports cin_no, date_range, mode, cycle_id
update_consumer_lps_waiver(cin_no: str, waiver_amount: float, reason_note: str, admin_name: str) -> None
```

### Charges Config Functions
```python
get_charges_config() -> dict
update_charges_config(new_rates: dict, admin_name: str, note: str) -> None  # saves history snapshot first; writes audit_log
apply_annual_increment(admin_name: str) -> None                  # multiplies all numeric rates × 1.10; writes audit_log
get_charges_config_history() -> list
```

### Meter Reader Functions
```python
create_meter_reader(data: dict, admin_name: str) -> str          # creates Firebase Auth user + Firestore doc
get_meter_reader(uid: str) -> dict | None
list_meter_readers(active_only: bool = False) -> list
update_meter_reader(uid: str, updates: dict, admin_name: str) -> None
deactivate_meter_reader(uid: str, admin_name: str) -> None       # disables Firebase Auth account + updates Firestore
reactivate_meter_reader(uid: str, admin_name: str) -> None
reset_meter_reader_password(uid: str, new_password: str, admin_name: str) -> None
```

### Custom Adjustment Functions
```python
add_custom_adjustment(cin_no: str, adj_type: str, amount: float, reason_note: str, admin_name: str, cycle_id: str = None) -> str
get_adjustments_for_consumer(cin_no: str) -> list
```

### Meter Replacement Functions
```python
record_meter_replacement(cin_no: str, old_serial: str, new_serial: str, replacement_date: str, new_initial_reading_kl: float, admin_name: str) -> str
get_meter_replacement_history(cin_no: str) -> list
```

### Audit + Report Functions
```python
write_audit_log(action_type: str, performed_by: str, target_doc: str, old_value, new_value) -> None
get_audit_log(filters: dict = None) -> list          # supports date_range, action_type, performed_by
get_meter_reader_activity(date_from, date_to, reader_uid=None, zone=None) -> list
get_billing_summary(cycle_id: str) -> dict
get_zone_collection_report(cycle_id: str) -> list
get_outstanding_balance_report() -> list
get_skipped_readings_report(cycle_id: str) -> list
export_full_data_backup() -> dict
```

---

## `utils.py`

Shared utilities for the Python app.

```python
def format_currency(amount: float) -> str:
    # Returns "₹1,234.56"

def format_kl(value: float) -> str:
    # Returns "12.34 KL"

def format_date(dt) -> str:
    # Accepts datetime / date / Firestore Timestamp → returns "DD-MM-YYYY"

def parse_date(s: str) -> date:
    # Parses "DD-MM-YYYY" → date object

def today_str() -> str:
    # Today as "DD-MM-YYYY"

def add_months(d: date, months: int) -> date:
    # Add N calendar months using dateutil.relativedelta
    # e.g. add_months(date(2025,3,31), 1) → date(2025,4,30)

def run_in_thread(fn, *args, callback=None, error_callback=None, widget=None, **kwargs):
    # Runs fn(*args, **kwargs) in a daemon thread.
    # On success: calls callback(result) on main thread via widget.after(0, ...) if widget provided.
    # On exception: calls error_callback(exception) on main thread if provided; otherwise prints traceback.

def generate_receipt_number() -> str:
    # Format: RJB-YYYYMMDD-XXXXXX (6-digit zero-padded random)

def load_pdf_template(template_name: str) -> str:
    # Loads template from pdf_templates/{template_name}.html; returns string

def render_pdf_to_bytes(html_string: str) -> bytes:
    # Renders HTML string to PDF bytes using WeasyPrint

def render_pdf_to_file(html_string: str, output_path: str) -> None:
    # Renders HTML to PDF and saves to output_path using WeasyPrint

def open_pdf(path: str) -> None:
    # Opens PDF with default viewer (os.startfile on Windows; subprocess on Linux/Mac)

def get_excel_template_consumers() -> bytes:
    # Returns openpyxl workbook bytes with correct CSD headers + one example row

def get_excel_template_payments() -> bytes:
    # Returns openpyxl workbook bytes with payment import headers

def get_excel_template_readings() -> bytes:
    # Returns openpyxl workbook bytes for bulk reading edit

# Constants
CONSUMER_STATUS_OPTIONS = ["Active", "Inactive", "Meter Faulty", "Disconnected", "Disputed"]
METER_SIZE_OPTIONS = ["15mm","20mm","25mm","40mm","50mm","80mm","100mm","150mm"]
CATEGORY_OPTIONS = ["Domestic", "Non-Domestic", "Industrial"]
APL_BPL_OPTIONS = ["APL", "BPL"]
ZONE_RANGE = range(1, 21)    # zones 1–20
```

---

## `billing_engine.py`

Pure Python billing calculator. No Firestore calls. Accepts rates as a dict (from `charges_config/current`). Mirrors `billing-engine.js` logic exactly — same calculations, same edge cases, same rounding.

```python
def calculate_bill(
    consumption_kl: float,
    consumer: dict,
    rates: dict,
    previous_outstanding: float = 0.0,
    credit_balance: float = 0.0,
    last_payment_date: date = None,
    payment_date: date = None,
    avg_6month_kl: float = None
) -> dict:
    """
    Returns full bill_breakdown dict with keys:
      water_charge, slab_details, minimum_charge_applied, minimum_charge_amount,
      fixed_charge, meter_service_charge, ids_charge, ids_rate_pct,
      previous_outstanding, credit_applied, remaining_credit,
      lps_amount, lps_type, lps_applicable,
      subtotal_before_lps, total_before_rounding, total_amount,
      is_anomaly, is_flat_rate_rural
    """

def get_slab_breakdown(consumption_kl: float, category: str, meter_size: str, rates: dict) -> list:
    """Returns list of {slab, kl, rate, amount} dicts."""

def apply_lps(bill_total: float, last_payment_date: date, payment_date: date, credit_balance: float, outstanding: float) -> dict:
    """Returns {lps_amount, lps_type, lps_applicable}"""
```

All rate values read from `rates` dict — never hardcode. The 2025 baseline values appear only as comments.

---

## `billing-engine.js`

JavaScript billing engine. ES6 module. Identical logic to `billing_engine.py`.

```javascript
// Default export
export default function calculateBill(consumptionKL, consumer, rates, previousOutstanding=0, creditBalance=0, lastPaymentDate=null, paymentDate=null, avg6MonthKL=null)

// Named exports
export function getSlabBreakdown(consumptionKL, category, meterSize, rates)
export function applyLPS(billTotal, lastPaymentDate, paymentDate, creditBalance, outstanding)
export function addMonths(date, months)    // add N calendar months (same logic as Python utils.add_months)
export function formatCurrency(amount)     // "₹1,234.56"
export function formatKL(value)            // "12.34 KL"
export function formatDate(dateObj)        // "DD-MM-YYYY" from JS Date
export function parseDate(str)             // "DD-MM-YYYY" → JS Date
```

All rates from `rates` parameter. No hardcoded values.

---

## `main.py`

Entry point for the Tkinter admin app.

**Admin Login:**
- On launch: show login dialog before main window
- Admin credentials stored in `admin_credentials.json` (sha256-hashed password)
- If file doesn't exist: show first-run setup to create credentials
- After 5 failed attempts: 30-second lockout
- Firebase Admin SDK initialized via `firebase_config.get_firebase_app()`

**Main Window:**
- Title: `"Rajasthan Jal Board — Admin Console"`
- `option_add("*Font", ("Segoe UI", 10))` at startup
- Left sidebar (~180px): nav buttons with emoji icons, active item highlighted
- Right area: content frame (swapped on nav click)
- Status bar bottom: admin name + current date

**Sidebar Nav (in order):**
```
🏠 Dashboard
👥 Consumers
👷 Meter Readers
💳 Billing Cycles
📖 Readings
💰 Payments
📊 Reports
⚙️  Charges Config
📋 Audit Log
```

**Dashboard (home screen):**
Fetched from Firestore in background thread on app start (auto-refresh every 5 minutes):
- Total active consumers
- Open billing cycles (zones, period, days remaining to last_payment_date)
- Pending correction queries count (red badge if > 0; orange alert with "Go to Readings" button)
- Pending readings in active cycles
- Total outstanding balance across all consumers (₹)
- Payments collected this month (₹)

Each stat in a card widget. "Refresh" button.

**Navigation:** Each nav button imports its module lazily and calls `module.get_frame(parent, fc, utils, be, admin)` where `fc=firebase_client`, `be=billing_engine`, `admin={"name":"Admin"}`.

---

## `consumers.py`

`get_frame(parent, fc, utils, be, admin) → ttk.Frame`

**ttk.Notebook tabs:**

**Tab 1 — Search/View:**
- Search by CIN No or Meter Serial (calls `fc.get_consumer` or `fc.get_consumer_by_meter_serial`)
- Results in `ttk.Treeview`
- Double-click → Consumer Detail popup (`Toplevel`):
  - Full CSD (read-only)
  - Buttons: Edit, Deactivate/Reactivate, View Ledger, Print CSD Sheet
  - **Print CSD Sheet:** generates PDF via WeasyPrint using `pdf_templates/csd_sheet.html`; loads template via `utils.load_pdf_template`, fills data with Python string substitution, renders via `utils.render_pdf_to_bytes`, opens with `utils.open_pdf`
  - Ledger tab inside popup: all readings, payments, adjustments, replacement history

**Tab 2 — Add Consumer:**
- All CSD fields with appropriate widgets
- Custom Attributes: sub-table widget for key-value pairs (Add Row / Remove Row buttons)
- Validation: cin_no required + unique; name required; category + meter_size required
- Save: `run_in_thread → fc.create_consumer`

**Tab 3 — Edit Consumer** (opened from detail popup or list):
- Same form as Add, pre-filled
- Save: `run_in_thread → fc.update_consumer`

**Tab 4 — Bulk Import:**
- "Download Template" button (Excel via `utils.get_excel_template_consumers()`)
- File picker → parse with openpyxl → validate → preview table → confirm → `fc.bulk_create_consumers`
- Progress bar; show errors per row

**Tab 5 — Export:**
- Zone filter (optional), status filter (optional)
- "Export to Excel" → `fc.list_consumers` → openpyxl workbook → save dialog

**Tab 6 — Meter Replacement:**
- Search by CIN No → auto-fills old serial, consumer name
- Fields: new meter serial, replacement date (DD-MM-YYYY), new initial reading (KL)
- Save: `fc.record_meter_replacement`

---

## `meter_readers.py`

`get_frame(parent, fc, utils, be, admin) → ttk.Frame`

**Layout:** Left panel = list of all readers (`ttk.Treeview`); Right panel = detail/edit form.

**Create Meter Reader** ("New" button → dialog):
- Fields: Name, Employee ID, Username (email becomes `username@rjb.local` if no `@` given), Password (shown once at creation — copy-to-clipboard button), Phone Number, Designation, Address, Zone (optional integer)
- Creates Firebase Auth user + Firestore doc via `fc.create_meter_reader`

**Edit:** All fields except UID/username inline in right panel; Save button.

**Reset Password:** Dialog → new password → `fc.reset_meter_reader_password`

**Deactivate/Reactivate:** Button → confirm → `fc.deactivate_meter_reader` or `reactivate_meter_reader` (disables Firebase Auth account).

**Filter:** "Active Only" checkbox on list.

---

## `charges_config.py`

`get_frame(parent, fc, utils, be, admin) → ttk.Frame`

**Layout:**
- Top: structured, readable rate table (grouped by category)
- "Last updated: [date] by [admin] — Note: [note]"
- Buttons: "Edit Rates", "Apply Annual 10% Increment", "View Change History"

**Edit Rates dialog:**
- All rate fields as number inputs, pre-filled with current values
- Requires admin to enter a change note before saving
- Confirm dialog showing what changed (old vs new)
- Calls `fc.update_charges_config`

**Annual Increment:**
- Confirmation: "This will multiply ALL rates by 1.10 from 1st April. Cannot be undone without manual correction. Confirm?"
- Calls `fc.apply_annual_increment`

**Change History dialog:** Table of `charges_config_history` entries.

**Live Bill Test Widget** (bottom of frame):
- Inputs: category, meter size, consumption (KL), last_payment_date, payment_date
- "Calculate" button → `be.calculate_bill` with current rates → show full breakdown

---

## `billing.py`

`get_frame(parent, fc, utils, be, admin) → ttk.Frame`

**ttk.Notebook tabs:**

**Tab 1 — Active Cycles:**
- Table of open cycles
- Per cycle: zones, billing period, **last_payment_date** (calculated, shown as "Last Pay By: DD-MM-YYYY"), days remaining
- Zone-wise progress: "X of Y consumers read" per zone
- Readings per reader today
- Skipped / Cannot Read count
- **"Close Cycle" button** per cycle → show close checklist (see Workflow section) → confirm → `fc.close_billing_cycle`

**Tab 2 — Initiate New Cycle:**

Form fields:
- **Zone(s):** multi-select `Listbox` (zones 1–20); zones in open cycles are greyed out + unselectable with tooltip "Already in active cycle"
- **Billing Period Start Date:** `Entry` (DD-MM-YYYY)
- **Billing Period End Date:** `Entry` (DD-MM-YYYY)
- **Grace Period:** `Radiobutton` — "1 Month" | "2 Months"

**Live Preview section** (auto-updates as fields are filled):
- Consumer count per selected zone (queried in background thread)
- **"Last Payment Date: [calculated date]"** shown prominently — updates instantly when end_date or grace_period changes
  - Calculated as: `end_date + grace_period_months` using `utils.add_months`
  - If dates are invalid: show "— (enter valid end date)"

"Initiate Cycle" button:
- Validation: zones selected, start/end dates valid, end > start, no zone conflicts
- Confirmation dialog: summary of cycle details + calculated last_payment_date + total consumer count
- On confirm: `fc.create_billing_cycle` (passes `grace_period_months` and the computed `last_payment_date` string)

**Tab 3 — CSD Sheet Print:**
- Select open cycle + zone(s)
- Preview: consumer count
- **"Generate & Open PDF" button:**
  - Background thread: fetch consumers for selected zones via `fc.list_consumers({"zone": zone})`
  - Load template: `utils.load_pdf_template("csd_sheet")`
  - Build combined HTML: loop over consumers, format each consumer's section, join with `page-break-after: always`
  - Render to PDF bytes via `utils.render_pdf_to_bytes`
  - Save to temp file → `utils.open_pdf`
- "Save As" button: save PDF to user-chosen path
- Progress bar during generation

**Tab 4 — Past Cycles:**
- Table of closed cycles (most recent first)
- Click → expand summary: zones, period, last_payment_date, grace_period_months, total billed, collected, consumer count

---

## `readings.py`

`get_frame(parent, fc, utils, be, admin) → ttk.Frame`

**ttk.Notebook tabs:**

**Tab 1 — View Readings:**
- Filters: Cycle (dropdown), Zone, Reader, Status (All / Finalized / Skipped / Cannot Read / Anomaly Flagged)
- `ttk.Treeview`: Date, Time, CIN, Name, Reader, Prev Reading, Curr Reading, Consumption, Total Bill, Status, Edited By Admin
- Click row → **Reading Detail popup:**
  - All reading fields + formatted bill breakdown
  - "Admin Override Edit" button:
    - Edit dialog: new current reading + required reason note
    - Show before/after bill comparison
    - Confirm → `fc.admin_update_reading` (recalculates bill, sets `edited_by_admin=True`)

**Bulk Edit via Excel:**
- "Download Readings" → export current cycle readings to Excel
- "Import Corrected Readings" → validate → preview changes → confirm → `fc.bulk_update_readings`

**Tab 2 — Pending Correction Queries:**
- Badge count on tab label (red if > 0)
- Table: Date, CIN, Consumer Name, Reader, Prev Reading, Submitted, Requested Corrected, Reason
- Per row: "Full Details" popup + "Approve" + "Reject" buttons
- Approve: confirm dialog → `fc.approve_correction_query`
- Reject: enter rejection note → `fc.reject_correction_query`

**Tab 3 — All Correction Queries:**
- Filter by cycle, status
- Same table with resolved items; click → detail popup

---

## `payments.py`

`get_frame(parent, fc, utils, be, admin) → ttk.Frame`

**ttk.Notebook tabs:**

**Tab 1 — Record Payment:**
- Fields: CIN No (search-as-you-type → auto-load consumer name + balances), Amount (₹), Payment Mode (Cash | E-Mitra), E-Mitra Key (shown only if E-Mitra), **Payment Date** (DD-MM-YYYY, defaults to today, **editable** — this date is used for LPS calculation), Cycle (optional dropdown), Notes (optional)
- Consumer info panel: name, outstanding_balance, credit_balance
- **LPS Preview:** based on payment_date entered vs the cycle's `last_payment_date` — show "No LPS" or "LPS: 10% = ₹X" or "LPS: 10% + interest = ₹X"
- Save → `fc.record_payment`
- On success: show receipt summary + **"Print Receipt PDF" button:**
  - Load `utils.load_pdf_template("payment_receipt")`
  - Fill all payment + consumer details via string substitution
  - Render via `utils.render_pdf_to_bytes`
  - Save to temp file + `utils.open_pdf`

**Tab 2 — Bulk Import:**
- Download template (utils.get_excel_template_payments())
- File picker → parse → validate → preview with LPS preview per row → confirm → `fc.bulk_record_payments`

**Tab 3 — Payment Log:**
- Filters: CIN No, Date Range, Mode (All/Cash/E-Mitra), Cycle
- `ttk.Treeview`: Receipt No, Date, CIN, Name, Amount, Mode, E-Mitra Key, Cycle, Received By
- "Export to Excel" button
- Click row → payment detail popup + "Reprint Receipt" button

**Tab 4 — LPS Waiver:**
- Search consumer by CIN
- Show outstanding, LPS amount, LPS type
- Waiver Type: Full | Partial; Waiver Amount; **Reason Note (required)**
- "Apply Waiver" → confirm → `fc.update_consumer_lps_waiver`

**Tab 5 — Credit Balance:**
- Search consumer → show credit_balance + outstanding_balance
- Add credit adjustment (amount + required reason note)
- Calls `fc.add_custom_adjustment(type="waiver")`
- History of credit adjustments for this consumer

---

## `reports.py`

`get_frame(parent, fc, utils, be, admin) → ttk.Frame`

**ttk.Notebook tabs (7 tabs):**

**Tab 1 — Meter Reader Activity:**
- Filters: Date Range, Reader (dropdown), Zone
- Table: Reader, Employee ID, CIN, Consumer Name, Date, Time, Prev (KL), Curr (KL), Consumption, Status
- Summary row: totals. Export to Excel.
- Source: `fc.get_meter_reader_activity`

**Tab 2 — Billing Summary:**
- Filter: Cycle (dropdown)
- Cards: Total Billed ₹, Collected ₹, Outstanding ₹, Consumer Count
- Zone breakdown table
- Bar chart (`matplotlib FigureCanvasTkAgg`): billed vs collected per zone
- Export to Excel. Source: `fc.get_billing_summary + fc.get_zone_collection_report`

**Tab 3 — Zone-wise Collection:**
- Filter: Cycle
- Table: Zone, Total, Read, Cannot Read, Pending, Billed ₹, Collected ₹, Collection %
- Bar chart (matplotlib). Export to Excel.

**Tab 4 — Outstanding Balance:**
- All consumers with `outstanding_balance > 0`
- Columns: CIN, Name, Zone, Category, Outstanding ₹, Months Overdue, LPS Status
- Sort by outstanding (desc). Export to Excel.
- **Print as PDF** button: renders `pdf_templates/consumer_ledger.html` (outstanding section only) via WeasyPrint

**Tab 5 — Skipped / Cannot Read:**
- Filter: Cycle. Table: CIN, Name, Zone, Reason, Reader, Date. Export to Excel.

**Tab 6 — Consumer Ledger:**
- Search: single consumer (CIN or Meter Serial) OR zone bulk export
- **Single consumer:** Full CSD + readings table + payments table + adjustments + replacement history + balances
  - "Export PDF" button: `pdf_templates/consumer_ledger.html` via WeasyPrint
  - "Export Excel" button
- **Zone/Bulk export:**
  - Zone selector + "Export All Ledgers to Excel" → one sheet per consumer
  - Progress bar

**Tab 7 — Full Data Backup:**
- Warning label. "Export Full Backup" button → `fc.export_full_data_backup` → openpyxl with one sheet per collection → save dialog. Progress bar.

---

## `audit_log.py`

`get_frame(parent, fc, utils, be, admin) → ttk.Frame`

- Filters: Date Range, Action Type, Performed By
- **"Load/Refresh" button** — NOT auto-loaded (avoids unnecessary reads)
- `ttk.Treeview`: Timestamp, Action Type, Performed By, Target Document, Old Value (truncated), New Value (truncated)
- Click row → detail popup: full old/new values as formatted JSON
- "Export to Excel" button

---

# WEBSITE FILE SPECIFICATIONS

---

## Shared rules for all 8 HTML files:

- Firebase JS SDK v9 modular from CDN (pick one version, use it everywhere)
- Link `style.css` from `<head>`
- Import `firebase_config.js` for Firebase project config
- **Auth guard:** every page checks `onAuthStateChanged` before rendering; redirect to `index.html` if not authenticated
- **Session storage keys:**
  - `"charges_config"` — object from `charges_config/current`, fetched on login
  - `"meter_reader_profile"` — `{uid, name, employee_id, zone}` fetched on login
  - `"active_zones"` — JSON array of zone integers from all open cycles, fetched on login and refreshed on `search.html` load
- **No list queries on the website** — only direct `getDoc` by cin_no or single-field indexed `getDocs` with `where()`
- Use `updateDoc` for partial updates — never `setDoc` on existing consumer docs
- All dates: DD-MM-YYYY; all amounts: ₹X,XXX.XX; all KL: X.XX KL
- Mobile-first; large touch targets (min 44px); `inputmode="decimal"` on KL number inputs

---

## `firebase_config.js`

```javascript
// TODO: Fill in your Firebase project credentials
export const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

---

## `style.css`

Single stylesheet. Government-utility aesthetic: clean, high contrast, readable in outdoor sunlight.

**Design tokens:**
```css
:root {
  --primary: #1a3a6b;
  --primary-light: #2d5aa0;
  --accent: #e8730a;
  --success: #2a7a2a;
  --danger: #c0392b;
  --bg: #f5f5f5;
  --card-bg: #ffffff;
  --text: #1a1a1a;
  --text-muted: #555555;
  --border: #cccccc;
  --font: 'Segoe UI', Arial, sans-serif;
}
```

**Include styles for:**
- Base reset, body, typography
- `.header` — fixed top bar: logo/title + logged-in user name + logout button
- `.container`, `.card`, `.section`
- `.nav-bar` — bottom mobile navigation bar (for website)
- `.form-group`, `label`, `input`, `select`, `textarea` — large, touch-friendly, min 44px height
- `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.btn-success` — large tap targets
- `.alert`, `.alert-warning` (orange, for consumer status flags), `.alert-danger`, `.alert-success`
- `.info-panel` — consumer info display, read-only fields
- `.bill-preview` — live bill breakdown table, right-aligned amounts, monospaced font for numbers
- `.status-badge` — colored pill for consumer status
- `.reading-input` — very large (font-size: 2rem), full-width numeric input for KL entry
- `.confirmation-box` — post-submit summary card
- `.timer-bar` — 5-minute countdown CSS progress bar (animated via JS width update)
- `.ledger-table` — bills/payments history table, striped rows, horizontally scrollable
- `.readings-log` — meter reader's own readings table
- `.loading-spinner` — centered spinner overlay
- `.error-message`, `.success-message`
- `.zone-warning` — grey disabled button style for "No Active Cycle" state
- Responsive: works on 375px mobile; all interactive elements have large tap targets; no hover-only interactions

---

## `index.html` — Login

**Flow:**
1. Show: RJB logo/title, "Meter Reader Login" heading, username input, password input, login button
2. Username: if no `@` in value, append `@rjb.local` automatically before passing to Firebase Auth
3. `signInWithEmailAndPassword`
4. On success:
   a. Fetch `meter_readers/{uid}` from Firestore
   b. Check `is_active` — if false: `signOut()` + show "Your account has been deactivated. Contact admin."
   c. Fetch `charges_config/current` → store in `sessionStorage["charges_config"]`
   d. Fetch all open billing cycles → extract flat zone array → store in `sessionStorage["active_zones"]`
   e. Store `{uid, name, employee_id, zone}` in `sessionStorage["meter_reader_profile"]`
   f. Redirect to `search.html`
5. On error: show user-friendly message (no Firebase error codes)
6. **Rate limiting:** track failed attempts in `localStorage["login_attempts"]` (count + first_attempt_time); after 5 failures within 15 minutes → show lockout countdown timer; disable login button

---

## `search.html` — Consumer Search

**On page load:**
- Auth check → if not authed, redirect to `index.html`
- **Re-fetch active zones** from Firestore (open cycles) → update `sessionStorage["active_zones"]`
  - This keeps zone status current without requiring re-login
- Show header with meter reader name + logout button
- Bottom nav bar: Home (🔍, active) | Ledger (📖) | My Readings (📋)

**Main content:**
- Large heading: "Search Consumer"
- Large full-width search input (`inputmode="text"`, placeholder: "Enter CIN No or Meter Serial Number")
- Search button; Clear button

**Search logic:**
1. Trim input; if empty: show "Please enter a CIN No or Meter Serial Number"
2. Try `getDoc(doc(db, "consumers", query))` — direct CIN lookup
3. If not found: `getDocs(query(collection(db, "consumers"), where("meter_serial_no", "==", queryValue)))` — returns at most 1 doc
4. Show loading spinner during queries
5. **If found:**
   - Show consumer info panel: Name, CIN, Zone, Category, Meter Size, Meter Serial, Address, Status, Last Reading (KL)
   - If `consumer_status` is NOT "Active": show `.alert-warning` banner with status text
   - **Check active zone:**
     - Read `active_zones` from sessionStorage
     - If `consumer.zone` IS in `active_zones`:
       - Show "Enter Reading" button (→ `reading.html?cin=XXX`) — styled `.btn-primary`
     - If `consumer.zone` is NOT in `active_zones`:
       - Show disabled grey button: `"No Active Cycle — Zone {zone}"` — styled `.zone-warning`
       - Show small note below: "Reading entry is only available when a billing cycle is active for this zone."
   - Always show "View Ledger" button (→ `ledger.html?cin=XXX`) regardless of zone status
6. **If not found:** show "No consumer found matching that CIN or Meter Serial Number."

---

## `reading.html` — Reading Entry

**URL param:** `?cin=XXX`

**On page load:**
1. Auth check
2. Load consumer: `getDoc(doc(db, "consumers", cin))` — show loading state
3. **Active zone re-check:** verify `consumer.zone` is in `sessionStorage["active_zones"]`
   - If not: show error "No active billing cycle for Zone X. Reading cannot be submitted." — hide form entirely
4. Fetch `charges_config` from `sessionStorage["charges_config"]`
5. Import `calculateBill` from `billing-engine.js`

**Layout:**
- Consumer info panel (read-only): CIN, Name, Category, Meter Size, Meter Serial, Status, Zone
- If status ≠ "Active": `.alert-warning` banner with status
- **Previous reading** shown prominently: `"Last Reading: XX.XX KL"` (large font)
- Reading Date: date input, defaults to today (DD-MM-YYYY format), editable
- **Current Reading input:** `.reading-input` class, `inputmode="decimal"`, `type="number"`, `step="0.001"`, min=0, placeholder "Enter current reading (KL)"
- Notes: optional text input
- "Cannot Read" button (secondary, grey) → `cannot-read.html?cin=XXX`

**Live bill preview** (updates on every keystroke in reading input):
```javascript
readingInput.addEventListener("input", () => {
  const curr = parseFloat(readingInput.value);
  const prev = consumer.last_reading;
  const consumption = curr - prev;

  if (isNaN(curr) || readingInput.value === "") {
    billPreview.innerHTML = ""; return;
  }
  if (consumption < 0) {
    showError("Current reading cannot be less than previous reading ("+formatKL(prev)+"). If the meter was replaced, tap 'Cannot Read' and inform admin.");
    submitBtn.disabled = true; return;
  }
  clearError();
  const breakdown = calculateBill(consumption, consumer, rates, consumer.outstanding_balance, consumer.credit_balance);
  renderBillPreview(breakdown);  // populates .bill-preview table
  checkAnomaly(consumption);
});
```

**Anomaly detection:**
- If `consumer.avg_6month_kl` exists and `consumption > 3 × consumer.avg_6month_kl`:
  - Show orange `.alert-warning`: `"⚠ Unusually high consumption: {consumption} KL (avg: {avg} KL). Please confirm this reading is correct."`
  - Render a required checkbox: `"I confirm the reading is correct"` — Submit disabled until checked
  - `anomaly_flagged = true` on the reading document

**Submit button:**
- Validation: reading entered, no negative consumption, anomaly confirmed if flagged
- Show loading state on button
- **Firestore write (in a batch/transaction):**
  ```
  Set readings/{newId}: {all reading fields, status="finalized", full_bill_breakdown, submitted_at=serverTimestamp(), edit_window_expiry = Timestamp(now + 5 min), anomaly_flagged}
  Update consumers/{cin_no}: {last_reading: curr, outstanding_balance: outstanding + total_amount}
  ```
- On success: `window.location.href = "confirmation.html?reading_id=" + newId`

---

## `confirmation.html` — Post-Submission

**URL param:** `?reading_id=XXX`

**On load:**
1. Auth check
2. Load reading from Firestore: `getDoc(doc(db, "readings", readingId))`
3. Load consumer: `getDoc(doc(db, "consumers", reading.cin_no))`

**Show `.confirmation-box`:**
```
✅ Reading Submitted Successfully
Consumer: {name} | CIN: {cin_no}
Reading Date: {reading_date}
Reading Submitted: {current_reading} KL
Previous Reading: {previous_reading} KL
Consumption: {consumption} KL
─────────────────────────────
Total Bill: ₹{total_amount}
[Expand for bill breakdown]
```

Collapsible `<details>` section shows full slab breakdown.

**5-Minute Edit Window:**
```javascript
function updateTimer() {
  const expiry = reading.edit_window_expiry.toDate();
  const remaining = expiry - new Date();
  if (remaining > 0) {
    const mins = Math.floor(remaining / 60000);
    const secs = Math.floor((remaining % 60000) / 1000);
    timerBar.style.width = (remaining / 300000 * 100) + "%";
    timerLabel.textContent = `Edit window: ${mins}:${secs.toString().padStart(2,"0")} remaining`;
    editBtn.style.display = "inline-block";
    correctionBtn.style.display = "none";
  } else {
    timerBar.style.width = "0%";
    timerLabel.textContent = "Edit window closed";
    editBtn.style.display = "none";
    correctionBtn.style.display = "inline-block";
  }
}
setInterval(updateTimer, 1000);
updateTimer();
```

**Edit button** (visible during window): redirects to `reading.html?cin=XXX&edit=XXX`
- `reading.html` detects `edit` param, pre-fills the form with existing reading
- On re-submit: **overwrites** the existing reading document (same ID) + recalculates bill + updates consumer outstanding atomically

**"Raise Correction Query" button** (visible after window): `correction.html?reading_id=XXX`

Bottom buttons: "Search Another" → `search.html` | "My Readings" → `my-readings.html`

---

## `correction.html` — Correction Query

**URL param:** `?reading_id=XXX`

1. Load reading from Firestore
2. Check if a correction query already exists for this `reading_id` — if so, show its status (pending/approved/rejected with rejection note) instead of the form

**Form (if no existing query):**
- Pre-filled read-only: Meter Reader name + employee_id, Consumer CIN + name, Previous Reading, Submitted Reading
- **Requested Corrected Reading (KL):** number input, required
- **Reason Note:** textarea, required
- Submit → write `correction_queries/{newId}` with `status="pending"` + all required fields
- On success: "Your correction query has been submitted. Admin will review it."

---

## `cannot-read.html` — Cannot Read Submission

**URL param:** `?cin=XXX`

1. Load consumer from Firestore
2. Show consumer info panel (read-only): CIN, Name, Zone, Status, Last Reading
3. Form:
   - Reason: `<select>` — "Locked Premises" | "Meter Faulty" | "Meter Not Found" | "Other"
   - Notes: optional `<textarea>`
4. Submit → write `readings/{newId}`:
   ```
   cin_no, reader_uid, reader_name, status="skipped",
   cannot_read_reason=reason, notes=notes,
   submitted_at=serverTimestamp(),
   current_reading=null, consumption=null, full_bill_breakdown=null
   ```
   **Do NOT update `consumers/{cin_no}` — `last_reading` stays unchanged**
5. On success: "Cannot Read recorded for [Name]." + "Search Another Consumer" button

---

## `ledger.html` — Consumer Ledger (Read-Only)

**URL param:** `?cin=XXX` (optional; if absent, show inline search box first)

**Load in parallel** (`Promise.all`):
1. `getDoc(doc(db, "consumers", cin))` — consumer info
2. `getDocs(query(collection(db,"readings"), where("cin_no","==",cin), where("submitted_at",">=", twelveMonthsAgo), orderBy("submitted_at","desc")))` — last 12 months readings
3. `getDocs(query(collection(db,"payments"), where("cin_no","==",cin), where("payment_date",">=", twelveMonthsAgoStr), orderBy("payment_date","desc")))` — last 12 months payments

Show loading skeletons per section while loading.

**Display (read-only — NO admin notes, NO other readers' activity):**
- Consumer info card: Name, CIN, Zone, Category, Meter Size, Meter Serial, Address, Contact, APL/BPL
- Balance row: "Outstanding: ₹X" | "Credit Balance: ₹X"
- Current cycle reading status: show if a reading exists for this consumer in any open cycle (check against `active_zones` + query readings by cin_no + cycle)
- **Bills table** (`.ledger-table`): Date, Consumption (KL), Total Bill (₹), Payment Status (Paid / Unpaid / Partial)
- **Payments table** (`.ledger-table`): Date, Amount (₹), Mode
- No adjustments, no admin notes shown

---

## `my-readings.html` — Meter Reader Log

**On load:** Auth check → show all readings by logged-in reader.

**Filters:** Date From, Date To (DD-MM-YYYY) — "Load" button.

**Query:**
```javascript
getDocs(query(
  collection(db, "readings"),
  where("reader_uid", "==", auth.currentUser.uid),
  where("submitted_at", ">=", fromTimestamp),
  where("submitted_at", "<=", toTimestamp),
  orderBy("submitted_at", "desc"),
  limit(50)
))
```

**Table** (`.readings-log`): Date, Time, Consumer CIN, Consumer Name, Consumption (KL), Total Bill (₹), Status, Query Status (None / Pending / Approved / Rejected)

- Click row → expand inline (using `<details>`) showing full bill breakdown (read-only)
- Query status badge: colored pill showing correction query status if any
- "Load More" button (Firestore cursor-based pagination with `startAfter`)

---

# FINAL IMPLEMENTATION NOTES

1. **WeasyPrint only** — no reportlab anywhere. All PDFs go through `pdf_templates/*.html` → `utils.render_pdf_to_bytes`.

2. **Last payment date is never manually entered** — it is always computed from `end_date + grace_period_months` and shown as a calculated preview. The `grace_period_months` value (1 or 2) is what the admin sets.

3. **Zone restriction on website is enforced at two levels:**
   - UI level: "Enter Reading" button disabled/replaced on search.html
   - Logic level: reading.html re-verifies before showing the form

4. **active_zones refreshed on every search.html load** — ensures meter readers see zone status changes without re-logging in.

5. **Background threads in Python app** — every `firebase_client` call in the Python GUI must go through `utils.run_in_thread`. Never call Firestore on the main thread.

6. **Atomic writes** — any write that modifies both a reading and `consumers/{cin_no}` must use a Firestore `WriteBatch` or transaction (Python app) or `writeBatch` (website JS).

7. **Firestore cost efficiency:**
   - `outstanding_balance` and `credit_balance` are denormalized on consumer doc — updated atomically on every payment/reading finalization
   - `last_reading` stored on consumer doc — no history query needed by website
   - Website never fetches a consumer list — only direct getDoc or single indexed field query
   - `charges_config` cached in sessionStorage after login — not re-fetched per consumer
   - Audit log written as append-only; never read in real-time on the website

8. **Bill breakdown written once** at reading finalization — not recalculated on every display. Exception: admin override edit in Python app recalculates and overwrites.

9. **Date format enforcement** — DD-MM-YYYY everywhere, in both Python and JS. Store as strings in Firestore for dates (not Timestamps) except for `submitted_at`, `created_at`, `updated_at` which use Firestore `serverTimestamp()`.

10. **Python app dependencies to install:**
    ```
    pip install firebase-admin openpyxl weasyprint matplotlib python-dateutil
    ```

11. **Firebase setup after build:**
    - Fill credentials in `firebase_config.py` and `public/firebase_config.js`
    - Create `charges_config/current` document in Firestore with 2025 baseline rates
    - Run `firebase deploy` to deploy rules + hosting
    - Run `python main.py` for the desktop admin app

---

*Build all files now, in the order listed in the FILE STRUCTURE section. Complete each file fully before moving to the next.*
