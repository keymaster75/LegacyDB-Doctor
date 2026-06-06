# Changelog

All notable changes to LegacyDB Doctor will be documented in this file.

## [Unreleased]

### Added
- Microsoft Access `.mdb` / `.accdb` database scanning through ODBC.
- Table and column inventory.
- Row count detection per table.
- Access/ODBC to MySQL type mapping.
- Excel migration-readiness report.
- MySQL `schema.sql` generation.
- Optional normalized MySQL-safe table and column names.
- Suspicious table name detection.
- Cleanup candidates sheet.
- Migration plan sheet.
- Primary key / unique index detection.
- Primary key status summary.
- Data quality sheet for empty and low-fill columns.
- Column fill-rate profiling.
- Warning comments for tables without primary key or unique index.
- CLI options for report-only, summary-only, output directory, and automatic report opening.
- CSV export command for Access user tables.
- CSV export manifest file (`_export_manifest.csv`).
- CSV table filtering with `--tables`.
- Empty-table skipping during CSV export with `--skip-empty`.
- Row-limited CSV export with `--limit`.
- CSV manifest `export_limit` column.
- CSV manifest `planned` status for manifest-only exports.
- CSV export dry-run mode with `--manifest-only`.
- Unit tests for summary building, identifier suggestions, SQL generation, CLI smoke test, CSV manifest writing, table filtering, and CSV export SQL generation.

### Changed
- Refactored scan summary generation into a shared summary builder.
- Improved generated SQL handling for recommended MySQL-safe identifiers.
- Improved CSV export documentation and test coverage.

### Fixed
- Handled Access/ODBC metadata decoding errors during column inspection.
- Handled empty CSV table filter results by still creating an export manifest.
- Avoided invalid trailing comma in generated SQL by moving no-primary-key warnings before `CREATE TABLE`.

## [0.1.0] - Planned

Initial public prototype release.
