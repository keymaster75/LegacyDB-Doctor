# Access to MySQL Migration Checklist

This checklist is intended for old business applications built around Access, Delphi, VB, or similar desktop technologies.

## Before migration

- Make a full backup of the original `.mdb` / `.accdb` file.
- Check whether the application uses linked tables.
- Check whether the database contains system tables or hidden tables.
- Identify all tables used by the application.
- Identify primary keys and relationships.
- Check for tables without primary keys.
- Check for duplicate business identifiers.
- Check text encoding and local characters.
- Check date formats.
- Check numeric columns that may contain text.
- Check yes/no fields.
- Check memo/long text fields.
- Check attachment/OLE fields.

## During migration

- Generate MySQL schema.
- Review column type mapping manually.
- Import data into a test database first.
- Compare row counts table by table.
- Run application-level smoke tests.
- Compare key reports before and after migration.

## After migration

- Keep the original Access database archived.
- Document any manual fixes.
- Create post-migration validation reports.
- Create backup procedure for the new MySQL/MariaDB database.
