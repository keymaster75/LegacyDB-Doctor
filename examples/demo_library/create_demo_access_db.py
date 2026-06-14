from __future__ import annotations

"""
Create the synthetic LegacyDB Doctor demo Access database.

This script is intentionally kept inside examples/demo_library and is not part of
the core LegacyDB Doctor runtime. It is a Windows-only helper for creating a
public, synthetic .mdb file that demonstrates migration-readiness findings.

Requirements:
- Windows
- Microsoft Access Database Engine / Access ODBC driver
- pyodbc
- pywin32 only if the database file must be created from scratch

Usage:
    python examples/demo_library/create_demo_access_db.py

Optional:
    python examples/demo_library/create_demo_access_db.py --out examples/demo_library/legacy_library_demo.mdb --overwrite
"""

import argparse
from pathlib import Path

import pyodbc


DEFAULT_DRIVER = "Microsoft Access Driver (*.mdb, *.accdb)"


def create_empty_mdb(database_path: Path) -> None:
    """
    Create an empty .mdb file using ADOX through pywin32.

    pywin32 is imported lazily so it does not become a project dependency.
    If this fails, create an empty .mdb manually in Microsoft Access and run
    the script again without --overwrite.
    """
    try:
        import win32com.client  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is required to create a new .mdb automatically. "
            "Install it with 'python -m pip install pywin32', or create an empty "
            ".mdb manually in Microsoft Access and run this script again."
        ) from exc

    database_path.parent.mkdir(parents=True, exist_ok=True)

    provider_errors: list[str] = []
    providers = [
        "Microsoft.ACE.OLEDB.12.0",
        "Microsoft.Jet.OLEDB.4.0",
    ]

    for provider in providers:
        try:
            catalog = win32com.client.Dispatch("ADOX.Catalog")
            catalog.Create(f"Provider={provider};Data Source={database_path};")
            return
        except Exception as exc:  # pragma: no cover - Windows COM environment specific
            provider_errors.append(f"{provider}: {exc}")

    joined_errors = "\n".join(provider_errors)
    raise RuntimeError(f"Could not create Access database using ADOX providers:\n{joined_errors}")


def connect_access(database_path: Path, driver: str = DEFAULT_DRIVER) -> pyodbc.Connection:
    connection_string = f"DRIVER={{{driver}}};DBQ={database_path};"
    return pyodbc.connect(connection_string, autocommit=True)


def execute_many(cursor: pyodbc.Cursor, statements: list[str]) -> None:
    for statement in statements:
        cursor.execute(statement)


def insert_rows(cursor: pyodbc.Cursor, sql: str, rows: list[tuple]) -> None:
    for row in rows:
        cursor.execute(sql, row)


def create_schema(cursor: pyodbc.Cursor) -> None:
    """
    Create demo tables using conservative Access/ODBC DDL.

    Access ODBC is picky about CREATE TABLE syntax. To keep the demo generator
    portable, table columns are created first and indexes are created separately.
    """
    execute_many(
        cursor,
        [
            """
            CREATE TABLE Author (
                AuthorID INTEGER,
                FullName VARCHAR(120),
                BirthYear INTEGER,
                NoteText VARCHAR(255)
            )
            """,
            """
            CREATE TABLE Book (
                BookID INTEGER,
                InventoryNumber INTEGER,
                Title VARCHAR(180),
                Subtitle VARCHAR(180),
                PublicationYear INTEGER,
                NoteText VARCHAR(255)
            )
            """,
            """
            CREATE TABLE Member (
                FullName VARCHAR(120),
                ClassName VARCHAR(30),
                Phone VARCHAR(50),
                Email VARCHAR(120),
                RegistrationDate DATETIME
            )
            """,
            """
            CREATE TABLE BookAuthor (
                BookID INTEGER,
                AuthorID INTEGER
            )
            """,
            """
            CREATE TABLE Member_ImportErrors (
                ErrorText VARCHAR(255),
                FieldName VARCHAR(120),
                RowNumber INTEGER
            )
            """,
            """
            CREATE TABLE Book_OldBackup (
                BookID INTEGER,
                InventoryNumber INTEGER,
                Title VARCHAR(180),
                Subtitle VARCHAR(180),
                PublicationYear INTEGER,
                NoteText VARCHAR(255)
            )
            """,
        ],
    )

    execute_many(
        cursor,
        [
            "CREATE UNIQUE INDEX ux_Author_AuthorID ON Author (AuthorID)",
            "CREATE UNIQUE INDEX ux_BookAuthor_BookID_AuthorID ON BookAuthor (BookID, AuthorID)",
            "CREATE INDEX ix_Book_InventoryNumber ON Book (InventoryNumber)",
        ],
    )


def insert_demo_data(cursor: pyodbc.Cursor) -> None:
    insert_rows(
        cursor,
        "INSERT INTO Author (AuthorID, FullName, BirthYear, NoteText) VALUES (?, ?, ?, ?)",
        [
            (1, "Mary Shelley", 1797, "Classic author"),
            (2, "Jules Verne", 1828, "Adventure fiction"),
            (3, "Nikola Tesla", 1856, "Science biography subject"),
            (4, "Jane Austen", 1775, None),
        ],
    )

    insert_rows(
        cursor,
        """
        INSERT INTO Book (BookID, InventoryNumber, Title, Subtitle, PublicationYear, NoteText)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (1, 10010, "Frankenstein", None, 1818, None),
            (2, 10011, "Journey to the Center of the Earth", None, 1864, None),
            (3, 10012, "Twenty Thousand Leagues Under the Seas", None, 1870, "duplicate demo"),
            (4, 10012, "Around the World in Eighty Days", None, 1872, "duplicate demo"),
            (5, 10013, "My Inventions", None, 1919, None),
            (6, 10014, "Pride and Prejudice", None, 1813, None),
        ],
    )

    insert_rows(
        cursor,
        """
        INSERT INTO Member (FullName, ClassName, Phone, Email, RegistrationDate)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("Alex Reader", "Grade 7A", None, None, "2024-09-01"),
            ("Mina Pages", "Grade 8B", None, None, "2024-09-03"),
            ("Luka Novel", "Grade 6C", None, None, "2024-09-05"),
            ("Sara Bookmark", "Grade 7A", None, None, "2024-09-06"),
            ("Petar Chapter", "Grade 8B", None, None, "2024-09-07"),
        ],
    )

    insert_rows(
        cursor,
        "INSERT INTO BookAuthor (BookID, AuthorID) VALUES (?, ?)",
        [
            (1, 1),
            (2, 2),
            (3, 2),
            (4, 2),
            (5, 3),
            (6, 4),
        ],
    )

    insert_rows(
        cursor,
        "INSERT INTO Member_ImportErrors (ErrorText, FieldName, RowNumber) VALUES (?, ?, ?)",
        [
            ("Type conversion failure", "RegistrationDate", 14),
            ("Required field missing", "FullName", 27),
        ],
    )

    insert_rows(
        cursor,
        """
        INSERT INTO Book_OldBackup (BookID, InventoryNumber, Title, Subtitle, PublicationYear, NoteText)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (101, 90001, "Old backup book", None, 1999, "stale backup row"),
            (102, 90002, "Another old backup book", None, 2000, None),
        ],
    )


def create_demo_database(database_path: Path, overwrite: bool = False, driver: str = DEFAULT_DRIVER) -> Path:
    if database_path.exists():
        if overwrite:
            database_path.unlink()
            create_empty_mdb(database_path)
        else:
            print(f"Using existing database file: {database_path}")
    else:
        create_empty_mdb(database_path)

    conn = connect_access(database_path, driver=driver)

    try:
        cursor = conn.cursor()
        create_schema(cursor)
        insert_demo_data(cursor)
        cursor.close()
    finally:
        conn.close()

    return database_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the synthetic LegacyDB Doctor demo Access database.")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "legacy_library_demo.mdb",
        help="Output .mdb path. Defaults to examples/demo_library/legacy_library_demo.mdb.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete and recreate the output .mdb if it already exists.",
    )
    parser.add_argument(
        "--driver",
        default=DEFAULT_DRIVER,
        help="Access ODBC driver name.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_path = create_demo_database(args.out, overwrite=args.overwrite, driver=args.driver)
    print(f"Demo Access database created: {database_path}")
    print()
    print("Next step:")
    print(f'legacydb-doctor scan "{database_path}" --summary-only --readiness-details --duplicate-key-details')


if __name__ == "__main__":
    main()
