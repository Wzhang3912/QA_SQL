def SQL_question_message(schema_info, question):
    """
    Construct a prompt message for LLM to generate a SQL query.

    Args:
        schema_info (str): A string representing the schema of a database. 
        question (str): The user's question.

    Returns:
        list[dict]: A list of message in a format for input to an LLM.
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


def question_answer_message(question, query, result):
    """
    Construct a prompt message for the LLM to generate answers based on the SQL query result.

    Args:
        question (str): The user's question.
        query (str): The SQL query obtained from LLM response.
        result (str): The result of the SQL query execution.

    Returns:
        list[dict]: A list of message in a format for input to an LLM.

    """

    content = f"""
    Given the following user question, corresponding SQL query,
    and SQL result, answer the user question directly, in 1-2 sentences.

    User Question: {question}
    SQL Query: {query}
    SQL Result: {result}
    """

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant for answering questions given query result."
        }, 
        {
            "role": "user", 
            "content": content
        }
    ]
    
    return messages
