# Demo Library Data Plan

This document describes the planned synthetic Access database used to demonstrate LegacyDB Doctor.

The demo uses English table and column names so the public GitHub repository is easier to understand for an international audience.

---

## Database name

```text
legacy_library_demo.mdb
```

---

## Tables

### 1. Author

Clean lookup table.

Purpose: demonstrate a healthy table that should be treated as `Ready`.

Suggested columns:

| Column | Notes |
|---|---|
| `AuthorID` | formal primary key or unique index |
| `FullName` | required text |
| `BirthYear` | optional numeric field |
| `Note` | optional text |

Expected result:

- PK status: `formal` or `unique_index`
- Convertability: `Ready`
- no duplicate key issues
- low cleanup risk

Example rows:

| AuthorID | FullName | BirthYear | Note |
|---:|---|---:|---|
| 1 | Mary Shelley | 1797 | Classic author |
| 2 | Jules Verne | 1828 | Adventure fiction |
| 3 | Nikola Tesla | 1856 | Science biography subject |

---

### 2. Book

Main book table with an intentional candidate-key duplicate.

Purpose: demonstrate duplicate key value detection.

Suggested columns:

| Column | Notes |
|---|---|
| `BookID` | may exist but should not be formal PK in the demo scenario if `InventoryNumber` is intended as the candidate issue |
| `InventoryNumber` | should look like a candidate key |
| `Title` | required text |
| `Subtitle` | completely empty or almost empty |
| `PublicationYear` | optional numeric field |
| `Note` | mostly empty |

Intentional issue:

```text
InventoryNumber = 10012
InventoryNumber = 10012
```

Expected result:

- `InventoryNumber` detected as candidate/unique key signal depending on the final structure
- duplicate key issue detected
- `Duplicate Key Values` sheet populated
- `Migration Checklist` warns/fails duplicate key review
- data quality finding for `Subtitle` or `Note`

Example rows:

| BookID | InventoryNumber | Title | Subtitle | PublicationYear | Note |
|---:|---:|---|---|---:|---|
| 1 | 10010 | Frankenstein |  | 1818 |  |
| 2 | 10011 | Journey to the Center of the Earth |  | 1864 |  |
| 3 | 10012 | Twenty Thousand Leagues Under the Seas |  | 1870 | duplicate demo |
| 4 | 10012 | Around the World in Eighty Days |  | 1872 | duplicate demo |
| 5 | 10013 | My Inventions |  | 1919 |  |

---

### 3. Member

Reader/member table without a reliable key.

Purpose: demonstrate `Blocked` convertability.

Suggested columns:

| Column | Notes |
|---|---|
| `FullName` | text |
| `ClassName` | text |
| `Phone` | optional text |
| `Email` | optional text |
| `RegistrationDate` | date/time |

Expected result:

- PK status: `none`
- Convertability: `Blocked`
- readiness score penalty
- `Migration Plan` explains that rows exist but no key was detected

Example rows must be synthetic only.

---

### 4. BookAuthor

Junction table between `Book` and `Author`.

Purpose: demonstrate composite unique index handling and relationship suggestions.

Suggested columns:

| Column | Notes |
|---|---|
| `BookID` | FK-like column |
| `AuthorID` | FK-like column |

Recommended index:

```text
UNIQUE(BookID, AuthorID)
```

Expected result:

- table has composite key signal
- individual `BookID` and `AuthorID` values may repeat
- duplicate detector should not flag individual columns as false positives
- potential relationship suggestions may point to `Book.BookID` and `Author.AuthorID`

Example rows:

| BookID | AuthorID |
|---:|---:|
| 1 | 1 |
| 2 | 2 |
| 3 | 2 |
| 4 | 2 |
| 5 | 3 |

---

### 5. Member_ImportErrors

Simulated Access import error table.

Purpose: demonstrate cleanup candidate detection.

Suggested columns:

| Column | Notes |
|---|---|
| `Error` | text |
| `Field` | text |
| `RowNumber` | numeric |

Expected result:

- cleanup candidate
- high priority review
- likely `Exclude` convertability status

---

### 6. Book_OldBackup

Simulated old backup/copy table.

Purpose: demonstrate stale/copy/backup table detection.

Suggested columns can mirror a subset of `Book`.

Expected result:

- cleanup candidate
- likely `Exclude` convertability status
- should be reviewed before migration

---

## Data quality triggers

At least one column should be completely empty:

```text
Book.Subtitle
```

At least one column should be less than 10 percent filled:

```text
Book.Note
```

Expected result:

- `Data Quality` sheet includes high/medium severity findings
- `Readiness Factors` includes a penalty for empty or almost empty columns

---

## Expected high-level result

The final demo should produce a mixed report:

| Area | Expected result |
|---|---|
| Ready table | `Author` |
| Blocked table | `Member` |
| Excluded cleanup tables | `Member_ImportErrors`, `Book_OldBackup` |
| Duplicate key issue | `Book.InventoryNumber` |
| Composite key false-positive avoidance | `BookAuthor` |
| Data quality issue | `Book.Subtitle`, `Book.Note` |
| Relationship suggestions | `BookAuthor.BookID`, `BookAuthor.AuthorID` |

The demo should be intentionally imperfect. Its purpose is to show that LegacyDB Doctor can explain legacy migration risk instead of silently pretending everything is ready.


---

## Implementation note

The helper script `create_demo_access_db.py` is intended to create and populate this database on Windows.

The first generated version should be treated as a test artifact until it is scanned with LegacyDB Doctor and the actual output is compared with the expected findings in this document.

If the actual scan result differs from the expected result, adjust the synthetic structure or this plan rather than using private real-world data.
