# Access to MySQL Type Mapping

Initial practical mapping used by LegacyDB Doctor.

| Access / ODBC type | Suggested MySQL type |
|---|---|
| COUNTER / AUTOINCREMENT | INT AUTO_INCREMENT |
| BYTE / TINYINT | TINYINT |
| SHORT / SMALLINT | SMALLINT |
| LONG / INTEGER / INT | INT |
| SINGLE / REAL | FLOAT |
| DOUBLE / FLOAT | DOUBLE |
| DECIMAL / NUMERIC / CURRENCY | DECIMAL(p,s) |
| BIT / YESNO / BOOLEAN | TINYINT(1) |
| DATETIME / DATE / TIME | DATETIME |
| TEXT / VARCHAR | VARCHAR(n) or TEXT |
| MEMO / LONGTEXT | TEXT |
| GUID | CHAR(36) |
| OLE / BINARY | LONGBLOB |

This mapping should always be reviewed before production migration.
