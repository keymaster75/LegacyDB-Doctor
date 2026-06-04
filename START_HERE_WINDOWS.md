# START HERE - Windows / PyCharm

## 1. Extract ZIP

Extract the project to a folder, for example:

```text
C:\Projects\LegacyDB-Doctor
```

## 2. Open in PyCharm

Open PyCharm → Open → select the extracted folder.

## 3. Create virtual environment

In PyCharm terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

then activate again.

## 4. Test CLI

```powershell
python -m legacydb_doctor --help
python -m legacydb_doctor drivers
```

The `drivers` command should show whether the Access ODBC driver is installed.

## 5. Scan Access database

```powershell
python -m legacydb_doctor scan "C:\path\to\your\database.mdb" --out report.xlsx --schema-out schema.sql
```

## 6. Connect to GitHub repository

From the project root:

```powershell
git init
git add .
git commit -m "Initial LegacyDB Doctor starter project"
git branch -M main
git remote add origin https://github.com/keymaster75/LegacyDB-Doctor.git
git push -u origin main
```

If GitHub says that the remote is not empty:

```powershell
git pull origin main --allow-unrelated-histories
```

then resolve conflicts if needed and push again.
