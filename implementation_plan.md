# Rajasthan Jal Board Consumer Management & Billing System - Implementation Plan

## Goal Description
Build a two-part billing and consumer management system for the Rajasthan Jal Board:
1. **Python Tkinter Desktop Application** for admin management (runs locally, manages consumers, meter readers, billing cycles, payments, reports, configurations, and audit logs).
2. **Firebase Hosted Website** for field meter readers (mobile-first, handles consumer lookup, live billing calculations, reading entry with anomaly detection, correction requests, and readings log).

Both applications interact with a shared Firebase project. Data integrity is maintained via Firestore transactions, security rules, and background threading for UI responsiveness.

---

## User Review Required

> [!IMPORTANT]
> **Firebase Credentials & Setup**:
> Both the Python admin app and the website require valid Firebase configurations. The code will expose configurations for `serviceAccountKey.json` (Python Admin SDK) and `firebase_config.js` (Web Client SDK). The admin will need to place `serviceAccountKey.json` in the Python application directory.

> [!WARNING]
> **WeasyPrint System Dependencies**:
> WeasyPrint requires additional system libraries (Pango, Cairo, GDK-PixBuf) on Windows. Follow these steps to install:
> 1. Run `pip install weasyprint` in your environment.
> 2. Download and run the GTK3 installer for Windows (e.g. from [GTK for Windows](https://github.com/tschoonj/GTK-for-Windows-runtime-environment-installer/releases) or via MSYS2: `pacman -S mingw-w64-x86_64-gtk3`).
> 3. Add the GTK3 `bin` directory to your system's PATH environment variable.

---

## Open Questions
All open questions have been resolved:
1. Python files will be placed in the `python_app/` subdirectory (approved by user).

---

## Proposed Changes

### Configuration and Rules
#### [NEW] [firestore.rules](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/firestore.rules)
- Implement rules for meter readers (Auth users) to allow read access to `consumers`, `billing_cycles`, and `charges_config`, write access to `readings` (only their own before `edit_window_expiry`), and `correction_queries` (only their own).
- Block access to payments, adjustments, and other reader configurations.

#### [NEW] [firebase.json](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/firebase.json)
- Configure Firebase hosting pointing to the `public` directory and firestore rules.

#### [NEW] [.firebaserc](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/.firebaserc)
- Set up target Firebase project (placeholder to be updated by user).

---

### PDF Templates
Save templates in `pdf_templates/` using standard A4/A5 styled HTML.
#### [NEW] [csd_sheet.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/pdf_templates/csd_sheet.html)
- A5 sheet template for field reading collection containing consumer profile details and blank boxes for reading details.
#### [NEW] [payment_receipt.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/pdf_templates/payment_receipt.html)
- A5 layout for printing EMitra or cash payment confirmations.
#### [NEW] [consumer_ledger.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/pdf_templates/consumer_ledger.html)
- Full-page A4 report for consumer history (readings, payments, adjustments, meter changes).

---

### Python App (`python_app/` or root)
We will organize logic into a single folder or root as preferred. Let's assume a dedicated subfolder or root. We'll use a `python_app/` subfolder.

#### [NEW] [firebase_config.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/firebase_config.py)
- Expose `get_firebase_app()` initialized with `serviceAccountKey.json`.

#### [NEW] [firebase_client.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/firebase_client.py)
- Expose all CRUD APIs for consumers, billing cycles, readings, correction queries, payments, charges config, and meter readers. Ensure atomic writes where balances are modified.

#### [NEW] [utils.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/utils.py)
- Date styling, currency styling (Indian Rupee), relativedelta math, Excel imports/exports (openpyxl templates), threading wrappers (`run_in_thread`), and PDF execution wrapper.

#### [NEW] [billing_engine.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/billing_engine.py)
- Tariff calculator incorporating slab-wise water charges, fixed charges, meter charges, IDS, and LPS (using the 10% and 18% annual interest rules).

#### [NEW] [main.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/main.py)
- Admin Login (with lockout and credentials initialization) and the primary navigation dashboard interface.

#### [NEW] [consumers.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/consumers.py)
- GUI for searching, editing, adding, importing, exporting consumers, and logging meter replacements.

#### [NEW] [meter_readers.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/meter_readers.py)
- GUI for managing field workers, adding credentials, resetting passwords, and deactivating accounts.

#### [NEW] [charges_config.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/charges_config.py)
- GUI for live pricing adjustments, historic logging, increment applications (10%), and testing rates.

#### [NEW] [billing.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/billing.py)
- Open/past billing cycles management, zone selectors with active checks, and WeasyPrint CSD generator.

#### [NEW] [readings.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/readings.py)
- Readings table explorer, Excel correction import/export, and correction query approve/reject handlers.

#### [NEW] [payments.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/payments.py)
- Record payments with dynamic LPS previews, print PDF receipts, run bulk Excel uploads, and adjust outstanding credit balances.

#### [NEW] [reports.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/reports.py)
- Dashboard analytics (bar charts), collection status, reader performance, skipped lists, and database backups.

#### [NEW] [audit_log.py](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/python_app/audit_log.py)
- Secure tracking interface for admin actions.

---

### Website (public/)
Government-style aesthetic (dark-blue/orange contrast) using HSL tailoring and mobile compatibility.

#### [NEW] [index.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/index.html)
- Standard login page with 5-attempt local rate limit. Downloads and saves rates, zones, and profile to `sessionStorage` on success.
#### [NEW] [search.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/search.html)
- Dynamic search screen by CIN or Serial, automatically pulling and updating open zone validation list.
#### [NEW] [reading.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/reading.html)
- Consumption and bill calculator with real-time UI previews. Highlights high-use anomalies and guards against negative readings.
#### [NEW] [confirmation.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/confirmation.html)
- Post-upload landing screen displaying billing breakdowns and a 5-minute countdown clock allowing correction rewrites.
#### [NEW] [correction.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/correction.html)
- Query entry panel for incorrect readings where the 5-minute window has closed.
#### [NEW] [cannot-read.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/cannot-read.html)
- Status logging for inaccessible premises or broken meters (marked "skipped").
#### [NEW] [ledger.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/ledger.html)
- Horizontal table showing 12-month records of bills and payments.
#### [NEW] [my-readings.html](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/my-readings.html)
- Paginated feed of readings logged by the current reader.
#### [NEW] [style.css](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/style.css)
- Unified government-utility styled mobile theme.
#### [NEW] [billing-engine.js](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/billing-engine.js)
- JS translation of Python billing logic (strict parity).
#### [NEW] [firebase_config.js](file:///c:/Users/Shubham/Documents/Developnment/Rajasthan%20jal%20board%20-%20antigravity/public/firebase_config.js)
- Hosting config file.

---

## Verification Plan

### Automated / Code Validation
- Test billing engine logic with positive, zero, boundary, and negative consumption values.
- Verify date-addition rules for leap years and end-of-month dates.

### Manual Verification
- Launch Python application (`python main.py`) and verify that first-run setup creates credentials and displays the login screen.
- Verify dashboard loading, consumer data input, Excel exports, billing cycle creation, PDF sheet/receipt printing, and reports view.
- Run local hosting (`firebase serve` or similar) to test user authentication, consumer search, live calculations on reading input, anomaly verification check, and the 5-minute edit window countdown.
