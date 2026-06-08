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
- CSV manifest validation for missing files, row-count mismatches, planned exports, skipped empty tables, and required columns.
- CSV export validation command `validate-csv`.
- Unit tests for potential relationship detection.
- Potential relationship count in scan summary.
- `Potential Relationships` Excel report sheet.
- Heuristic potential relationship detection for legacy databases without formal foreign keys.
- Formal Access relationship metadata reader using ODBC and `MSysRelationships` fallback.
- Unit tests for summary building, identifier suggestions, SQL generation, CLI smoke test, CSV manifest writing, table filtering, and CSV export SQL generation.
- Windows quick start guide (`START_HERE_WINDOWS.md`) with setup, first scan, CSV export, and validation workflow.
- README link to the Windows quick start guide.

### Changed
- Refactored scan summary generation into a shared summary builder.
- Improved generated SQL handling for recommended MySQL-safe identifiers.
- Improved CSV export documentation and test coverage.
- Improved Excel migration-readiness report with potential relationship analysis.
- Improved README setup instructions and Rich-style terminal examples.
- Updated README report sheet list and roadmap to reflect implemented CSV validation and potential relationship reporting.
- Documented Windows PowerShell virtual environment activation note.
- Replaced `requirements.txt` dependency duplication with installation guidance.
- Moved dependency management to `pyproject.toml` with a `dev` extra for test dependencies.

### Fixed
- Handled Access/ODBC metadata decoding errors during column inspection.
- Handled empty CSV table filter results by still creating an export manifest.
- Avoided invalid trailing comma in generated SQL by moving no-primary-key warnings before `CREATE TABLE`.

## [0.1.0] - Planned

Initial public prototype release.
