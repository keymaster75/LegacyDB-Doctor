# Create the Demo Access Database

This document explains how to create the synthetic `legacy_library_demo.mdb` file used by the demo library scenario.

The database is intentionally imperfect. It exists to demonstrate LegacyDB Doctor findings such as:

- `Ready` tables
- `Blocked` tables
- cleanup candidates
- duplicate candidate/key values
- composite unique index handling
- data quality issues
- CSV export and import-script workflow

The demo data is synthetic and uses English names for a wider public audience.

---

## Option A: create the database automatically

From the repository root:

```powershell
python examples\demo_library\create_demo_access_db.py --overwrite
```

Expected output:

```text
Demo Access database created: examples\demo_library\legacy_library_demo.mdb
```

Then run:

```powershell
legacydb-doctor scan "examples\demo_library\legacy_library_demo.mdb" --summary-only --readiness-details --duplicate-key-details
```

Generate full outputs:

```powershell
legacydb-doctor scan "examples\demo_library\legacy_library_demo.mdb" --output-dir "examples\demo_library\out" --use-recommended-names
```

---

## Requirements

Automatic creation requires:

- Windows
- Microsoft Access Database Engine / Access ODBC driver
- `pyodbc`
- `pywin32` if the `.mdb` file does not already exist

Install `pywin32` only when you need to create the `.mdb` file automatically:

```powershell
python -m pip install pywin32
```

`pywin32` is intentionally not a core LegacyDB Doctor dependency.

---

## Option B: create an empty .mdb manually

If automatic `.mdb` creation does not work on your machine:

1. Open Microsoft Access.
2. Create a blank `.mdb` database.
3. Save it as:

```text
examples\demo_library\legacy_library_demo.mdb
```

4. Run the script without `--overwrite`:

```powershell
python examples\demo_library\create_demo_access_db.py
```

The script will use the existing empty database file and create/populate the demo tables.

---

## Safety note

Do not commit generated reports, exported CSV files, SQL output, or private databases.

Before committing, run:

```powershell
git status
git ls-files | findstr /i /r "\.mdb$ \.accdb$ \.xlsx$ \.xls$ \.sql$"
```

Only the synthetic demo `.mdb` may be considered for public inclusion after it is reviewed.
