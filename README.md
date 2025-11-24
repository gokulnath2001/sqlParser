# SQL Query Analyzer

A Python script to parse SQL queries and extract table names, JOIN conditions, and WHERE clauses. Exports results to CSV files.

## Features

- Extracts table names (including schema.table format)
- Identifies JOIN conditions with alias resolution
- Captures WHERE clause conditions
- Handles UNION queries
- Exports each query to a separate CSV file
- Supports multiple queries in a single file

## Requirements

- Python 3.6+
- `sqlparse` library

## Installation

1. Install Python 3 (if not already installed)
2. Install required package:
```bash
pip install sqlparse
```

**Or use requirements.txt:**
```bash
# 1. Install dependency
pip install -r requirements.txt

# 2. Run the script
python3 lalz.py your_file.sql
```

## Usage

### Command Line with File Path
```bash
# SQL or TXT files
python3 lalz.py your_queries.sql
python3 lalz.py your_queries.txt

# CSV files
python3 lalz.py your_queries.csv
```

### Interactive Mode
```bash
python3 lalz.py
# Then enter the file path when prompted
```

### Input File Formats

#### SQL/TXT Files
- Supports `.sql` or `.txt` files
- Multiple queries should be separated by semicolons (`;`)
- Comments (`--`) are automatically removed from output

#### CSV Files
- Supports `.csv` files
- Each cell can contain one or multiple SQL queries
- Multiple queries in a cell should be separated by semicolons (`;`)
- All rows and columns are processed
- Each query is tracked with its location (Row X, Col Y)

## Output

The script creates a `query_outputs/` directory containing:
- One CSV file per query
- File naming: `{filename}_query_{number}_{timestamp}.csv`

### CSV Columns
1. **Query** - Full SQL query (cleaned, single line)
2. **Table Names** - All tables used (comma + newline separated)
3. **JOIN Conditions** - All JOIN conditions (comma + newline separated)
4. **WHERE Conditions** - All WHERE conditions (comma + newline separated)

## Examples

### Example 1: SQL File
```bash
python3 lalz.py sample_queries.sql
```

Output:
```
Found 6 queries in the file
...
✓ Exported to: query_outputs/sample_queries_query_1_20251125_120000.csv
✓ All CSV files saved to: query_outputs/
```

### Example 2: CSV File
```bash
python3 lalz.py sample_input.csv
```

Output:
```
Found 13 queries in the file

### QUERY 1 ###
Location: Row 2, Col 1
Query: SELECT customer_id, customer_name FROM customers WHERE status = 'active';
...
Tables: ['customer_id', 'customer_name', 'customers', 'status']
JOIN Conditions: []
WHERE Conditions: ["status = 'active';"]
✓ Exported to: query_outputs/sample_input_query_1_20251125_120000.csv
...
```

**Note**: CSV files show the location (Row, Column) for each query found.

## Features in Detail

### Schema.Table Support
Correctly identifies tables in `schema.table_name` format:
- `DSA.COMM_TXN_V` → Extracted as full name
- `mstr_prod.SML` → Extracted as full name

### Alias Resolution
Replaces aliases with actual table names in conditions:
- Query: `FROM orders o WHERE o.status = 'active'`
- Output: `WHERE orders.status = 'active'`

### UNION Query Handling
Detects and processes all SELECT statements in UNION queries, extracting tables and conditions from all parts.

## Troubleshooting

**Error: No module named 'sqlparse'**
```bash
pip install sqlparse
```

**Error: File not found**
- Ensure the file path is correct
- Use absolute path or run from the correct directory

## Notes

- The script recursively searches for tables in nested queries
- Comments in SQL files are removed from CSV output
- Empty queries are automatically filtered out
- CSV files can be opened in Excel, Google Sheets, etc.

## Author

Created for SQL query analysis and documentation purposes.
