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
                # Get the full table name (including schema if present)
                # Check if it has schema.table format
                token_str = str(token).split()[0]  # Get first part (before alias)
                
                # Use get_real_name() which returns just the table name
                table_name = token.get_real_name()
                
                # Check if the original token has schema prefix
                if '.' in token_str and not token.has_alias():
                    # This is schema.table without alias
                    full_table_name = token_str
                elif '.' in token_str and token.has_alias():
                    # This is schema.table with alias - extract schema.table part
                    full_table_name = token_str
                else:
                    # No schema, just table name
                    full_table_name = table_name
                
                tables.append(full_table_name)
                
                # Check if there's an alias
                if token.has_alias():
                    alias = token.get_alias()
                    alias_to_table[alias] = full_table_name
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

def process_sql_file(file_path, output_dir="query_outputs"):
    """Read SQL file and process each query separately"""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Split queries using sqlparse (handles semicolons properly)
        statements = sqlparse.split(content)
        
        # Filter out empty statements
        queries = [stmt.strip() for stmt in statements if stmt.strip()]
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"Found {len(queries)} queries in the file\n")
        print("=" * 80)
        
        # Get base filename without extension
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for idx, query in enumerate(queries, 1):
            print(f"\n### QUERY {idx} ###")
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
                    table_names = ',\n'.join(tables)
                    join_conds = ',\n'.join(join_conditions) if join_conditions else 'No JOIN conditions'
                    where_conds = ',\n'.join(where_conditions) if where_conditions else 'No WHERE conditions'
                    
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