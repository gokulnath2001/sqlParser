import sqlparse
import csv
import os
from datetime import datetime

def extract_sql_info(sql_query):
    # Parse the SQL query
    parsed_query = sqlparse.parse(sql_query)[0]
    
    # Check if query contains UNION
    has_union = 'UNION' in sql_query.upper()

    # Extract table names and build alias mapping
    tables = []
    alias_to_table = {}
    
    def extract_from_tokens(tokens):
        """Recursively extract tables from tokens"""
        for token in tokens:
            if isinstance(token, sqlparse.sql.Identifier):
                # Get the full token string
                token_str = str(token).strip()
                
                # Check if there's an alias
                if token.has_alias():
                    alias = token.get_alias()
                    # Get the real table name (without alias)
                    table_name = token.get_real_name()
                    
                    # Check if it has schema.table format by looking at the token structure
                    # token_str format: "schema.table alias" or "table alias"
                    # We need to extract everything before the alias
                    if ' ' in token_str:
                        # Split by spaces and remove the last part (alias)
                        parts = token_str.rsplit(None, 1)  # Split from right, max 1 split
                        if len(parts) == 2:
                            full_table_name = parts[0]  # Everything before the alias
                        else:
                            full_table_name = table_name
                    else:
                        full_table_name = table_name
                    
                    alias_to_table[alias] = full_table_name
                else:
                    # No alias - use the full token string as-is
                    full_table_name = token_str
                
                tables.append(full_table_name)
            elif hasattr(token, 'tokens'):
                # Recursively search nested tokens (for UNION queries)
                extract_from_tokens(token.tokens)
    
    extract_from_tokens(parsed_query.tokens)

    # Extract column names
    columns = []
    
    def extract_columns_from_tokens(tokens):
        """Recursively extract columns from tokens"""
        for token in tokens:
            if isinstance(token, sqlparse.sql.IdentifierList):
                for identifier in token.get_identifiers():
                    # Check if it's an Identifier object before calling get_real_name()
                    if isinstance(identifier, sqlparse.sql.Identifier):
                        columns.append(identifier.get_real_name())
                    else:
                        # For Token objects, just use the string value
                        columns.append(str(identifier).strip())
            elif hasattr(token, 'tokens'):
                # Recursively search nested tokens
                extract_columns_from_tokens(token.tokens)
    
    extract_columns_from_tokens(parsed_query.tokens)

    # Extract JOIN conditions and WHERE conditions
    join_conditions = []
    where_conditions = []
    
    # Track if we've seen an ON keyword (indicates next Comparison is a JOIN condition)
    expecting_join_condition = False
    
    def extract_conditions_from_tokens(tokens):
        """Recursively extract conditions from tokens"""
        nonlocal expecting_join_condition
        
        for token in tokens:
            # Check if this is an ON keyword
            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'ON':
                expecting_join_condition = True
            
            # Extract JOIN conditions (Comparison tokens after ON keyword)
            elif isinstance(token, sqlparse.sql.Comparison) and expecting_join_condition:
                join_conditions.append(str(token).strip())
                expecting_join_condition = False
            
            # Extract WHERE conditions (Comparison tokens inside Where clause)
            elif isinstance(token, sqlparse.sql.Where):
                where_str = str(token).replace('WHERE', '').strip()
                where_conditions.append(where_str)
            
            # Recursively search nested tokens
            elif hasattr(token, 'tokens'):
                extract_conditions_from_tokens(token.tokens)
    
    extract_conditions_from_tokens(parsed_query.tokens)
    
    # Replace aliases with actual table names in conditions
    def replace_aliases(condition_str, alias_map):
        result = condition_str
        # Sort aliases by length (descending) to avoid partial replacements
        for alias in sorted(alias_map.keys(), key=len, reverse=True):
            # Replace alias. prefix with table_name. prefix
            result = result.replace(f"{alias}.", f"{alias_map[alias]}.")
        return result
    
    join_conditions = [replace_aliases(cond, alias_to_table) for cond in join_conditions]
    where_conditions = [replace_aliases(cond, alias_to_table) for cond in where_conditions]
    
    conditions = where_conditions

    return tables, columns, join_conditions, conditions, has_union

def process_csv_file(file_path, output_dir="query_outputs"):
    """Read CSV file and process queries from each cell"""
    try:
        all_queries = []
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row_idx, row in enumerate(reader, 1):
                for col_idx, cell in enumerate(row, 1):
                    if cell.strip():
                        # Split queries in this cell
                        cell_queries = sqlparse.split(cell)
                        for query in cell_queries:
                            query = query.strip()
                            if query:
                                # Store query with its location
                                all_queries.append({
                                    'query': query,
                                    'location': f"Row {row_idx}, Col {col_idx}"
                                })
        
        return all_queries
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def process_sql_file(file_path, output_dir="query_outputs"):
    """Read SQL/TXT/CSV file and process each query separately"""
    try:
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            # Process CSV file
            query_data = process_csv_file(file_path, output_dir)
            queries = [q['query'] for q in query_data]
            query_locations = [q['location'] for q in query_data]
        else:
            # Process SQL/TXT file
            with open(file_path, 'r') as file:
                content = file.read()
            
            # Split queries using sqlparse (handles semicolons properly)
            statements = sqlparse.split(content)
            
            # Filter out empty statements
            queries = [stmt.strip() for stmt in statements if stmt.strip()]
            query_locations = [None] * len(queries)  # No location info for SQL files
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"Found {len(queries)} queries in the file\n")
        print("=" * 80)
        
        # Get base filename without extension
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for idx, query in enumerate(queries, 1):
            location = query_locations[idx - 1]
            print(f"\n### QUERY {idx} ###")
            if location:
                print(f"Location: {location}")
            print(f"Query Preview: {query[:100]}..." if len(query) > 100 else f"Query: {query}")
            print("-" * 80)
            
            try:
                tables, columns, join_conditions, where_conditions, has_union = extract_sql_info(query)
                
                if has_union:
                    print("⚠️  UNION query detected - results include data from all SELECT statements")
                
                print(f"Tables: {tables}")
                print(f"Columns: {columns}")
                print(f"JOIN Conditions: {join_conditions}")
                print(f"WHERE Conditions: {where_conditions}")
                print("=" * 80)
                
                # Create CSV file for this query
                csv_filename = f"{output_dir}/{base_filename}_query_{idx}_{timestamp}.csv"
                with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(['Query', 'Table Names', 'JOIN Conditions', 'WHERE Conditions'])
                    
                    # Prepare data
                    # Remove SQL comments (-- style) and format query
                    query_lines = query.split('\n')
                    cleaned_lines = []
                    for line in query_lines:
                        # Remove inline comments
                        if '--' in line:
                            line = line[:line.index('--')]
                        line = line.strip()
                        if line:  # Only add non-empty lines
                            cleaned_lines.append(line)
                    query_text = ' '.join(cleaned_lines)
                    
                    # Join with comma and newline for each item to appear on separate line in CSV cell
                    # Filter out None values and convert all to strings
                    table_names = ',\n'.join([str(t) for t in tables if t is not None])
                    join_conds = ',\n'.join([str(j) for j in join_conditions if j is not None]) if join_conditions else 'No JOIN conditions'
                    where_conds = ',\n'.join([str(w) for w in where_conditions if w is not None]) if where_conditions else 'No WHERE conditions'
                    
                    # Write data row
                    writer.writerow([query_text, table_names, join_conds, where_conds])
                
                print(f"✓ Exported to: {csv_filename}")
                
            except Exception as e:
                print(f"Error processing query: {e}")
                print("=" * 80)
        
        print(f"\n✓ All CSV files saved to: {output_dir}/")
                
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
    except Exception as e:
        print(f"Error reading file: {e}")

# Main execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # File path provided as command line argument
        file_path = sys.argv[1]
    else:
        # Prompt for file path
        file_path = input("Enter the path to SQL file (.sql or .txt): ").strip()
    
    process_sql_file(file_path)