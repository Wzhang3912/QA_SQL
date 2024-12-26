import psycopg2
from psycopg2.extensions import cursor
from typing import Tuple

def get_cursor(
        database: str,
        host: str = "localhost", 
        user: str = "postgres", 
        password: str = "admin", 
        port: int = 5432
    ) -> cursor:
    """
    Establish connection to a PostgreSQL database

    Args:
        database (str): The name of the database to connect to.
        host (str): The hostname or IP address of the database server.
        user (str): The username to authenticate with the database.
        password (str): The password to authenticate with the database.
        port (int): The port number database server is listening.

    Returns:
        cursor: A cursor object used for executing SQL queries.
    """
    # Establish a connection to the database
    connection = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        port=port
    )
    print("Connection successful!\n")
    cursor = connection.cursor()

    return cursor


def get_schema_info(db_name: str) -> str:
    """
    Get SQL schema for the given PostgreSQL database.

    This function retrieves information about the database schema and 
    formats it into `CREATE TABLE` statements.

    Args:
        db_name (str): The name of the database to connect to.

    Returns:
        str: A formatted string containing SQL schema. 
    
        Example Output:
            CREATE TABLE my_table (
                column1 INTEGER NOT NULL,
                column2 VARCHAR(50),
                PRIMARY KEY (column1),
                FOREIGN KEY (column2) REFERENCES other_table(column1)
            );
    """

    with get_cursor(db_name) as cur:
        # Fetch columns and attributes
        sql_columns = """
            SELECT 
                c.table_schema,
                c.table_name,
                c.column_name,
                c.data_type,
                COALESCE(character_maximum_length, numeric_precision) AS length,
                c.is_nullable,
                c.column_default
            FROM 
                information_schema.columns c
            WHERE 
                c.table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY 
                c.table_schema, c.table_name, c.ordinal_position;"""

        cur.execute(sql_columns)
        columns = cur.fetchall()

        # Fetch primary key
        sql_primary_key = """
            SELECT 
                kcu.table_schema,
                kcu.table_name,
                kcu.column_name
            FROM 
                information_schema.table_constraints tco
            JOIN 
                information_schema.key_column_usage kcu
                ON tco.constraint_name = kcu.constraint_name
            WHERE 
                tco.constraint_type = 'PRIMARY KEY'
                AND tco.table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY 
                kcu.table_schema, kcu.table_name, kcu.ordinal_position;"""

        cur.execute(sql_primary_key)
        primary_keys = cur.fetchall()

        # Fetch foreign keys
        sql_foreign_key = """
            SELECT 
                tc.table_schema AS source_schema,
                tc.table_name AS source_table,
                kcu.column_name AS source_column,
                ccu.table_schema AS target_schema,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column
            FROM 
                information_schema.table_constraints AS tc
            JOIN 
                information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN 
                information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE 
                tc.constraint_type = 'FOREIGN KEY'
            ORDER BY 
                source_schema, source_table;"""

        cur.execute(sql_foreign_key)
        foreign_keys = cur.fetchall()
        
        # Format data into CREATE TABLE statements
        tables = {}
        for _, table, column, data_type, length, is_nullable, default in columns:
            if table not in tables:
                tables[table] = {
                    "columns": [],
                    "primary_keys": [],
                    "foreign_keys": []
                }
            column_def = f"{column} {data_type}"
            if length:
                column_def += f"({length})"
            if is_nullable == "NO":
                column_def += " NOT NULL"
            # if default:
            #     column_def += f" DEFAULT {default}"
            tables[table]["columns"].append(column_def)

        for _, table, column in primary_keys:
            tables[table]["primary_keys"].append(column)

        for _, source_table, source_column, _, target_table, target_column in foreign_keys:
            fk = f"FOREIGN KEY ({source_column}) REFERENCES {target_table}({target_column})"
            tables[source_table]["foreign_keys"].append(fk)

        create_statements = []
        for table, info in tables.items():
            create_statement = f"CREATE TABLE {table} (\n  "
            create_statement += ",\n  ".join(info["columns"])
            if info["primary_keys"]:
                create_statement += f",\n  PRIMARY KEY ({', '.join(info['primary_keys'])})"
            if info["foreign_keys"]:
                create_statement += f",\n  " + ",\n  ".join(info["foreign_keys"])
            create_statement += "\n);"
            create_statements.append(create_statement)

    return "\n\n".join(create_statements)


def execute_sql(
        sql_statement: str, db_name: str
    ) -> Tuple[list[Tuple], list[str]]:
    """
    Execute an SQL statement for the given database and retrieve results.

    Args:
        sql_statement (str): The SQL query to be executed.
        db_name (str): The name of the database to connect to.

    Returns:
        - result (list[tuples]): The rows returned by executing the query.
        - columns_header (list[str]): The column header of the result.
    """
    with get_cursor(db_name) as cur:
        cur.execute(sql_statement)
        result = cur.fetchall()
        columns_header = [desc[0] for desc in cur.description]

    return result, columns_header


def format_output(
        result: list[Tuple], col_header: list[str]
    ) -> str:
    """
    Format raw database output into table format.

    Args:
        result (list[tuple]): The rows returned by the query.
        col_header (list[str]): The column headers of the result.

    Returns:
        str: A string representation of the data formatted as a table.
    """

    table = ''

    # Determine max widths for each column
    col_widths = [
        int(max(len(str(row[i])) for row in result + [col_header])*1.5) for i in range(len(col_header))
    ]

    line = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
    header = "| " + " | ".join(f"{col_header[i]:{col_widths[i]}}" for i in range(len(col_header))) + " |"
    table += f'{line}\n{header}\n{line}\n'

    # Append the table rows
    for row in result:
        row_str = "| " + " | ".join(f"{str(row[i]):{col_widths[i]}}" for i in range(len(row))) + " |"
        table += row_str + '\n'

    # Bottom row
    table += line

    return table


def detect_keyword(sql_statement: str) -> str | None:
    """
    Detect if keyword present in the sql statement
    """
    KEYWORDS = ['INSERT INTO', 'UPDATE', 'DELETE FROM', 'CREATE TABLE', 'DROP TABLE', 'ALTER TABLE', 'TRUNCATE TABLE']

    for keyword in KEYWORDS:
        if keyword in sql_statement.upper():
            return keyword
    
    return None

