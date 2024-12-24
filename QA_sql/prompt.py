def message_construct(schema_info, question):
    """
    Construct a prompt message to for LLM in generating a SQL query.

    Args:
        schema_info (str): A string representing the schema of a database. 
        question (str): The user's question.

    Returns:
        list[dict]: A list of message objects in a format for input to an LLM.

    """

    content = f"""
    Your task is to convert a question into a syntactically correct SQL query, given a Postgres database schema.
    Adhere to these rules:
    - **Deliberately go through the question and database schema word by word** to appropriately answer the question
    - **Use Table Aliases** to prevent ambiguity. For example, `SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.
    - When creating a ratio, always cast the numerator as float

    Input:
    Generate a SQL query that answers the question: `{question}`.
    This query will run on a database whose schema is represented in this json format:

    {schema_info}
    """

    messages = [
        {
            "role": "system",
            "content": """
    You are a helpful assistant for generating SQL queries.
    Pay attention to use only the column names that you can see in the schema description. 
    Be careful to not query for columns that do not exist. 
    Also, pay attention to which column is in which table. 
    """
        }, 
        {
            "role": "user", 
            "content": content
        }
    ]

    return messages