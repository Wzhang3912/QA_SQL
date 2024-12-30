from typing import Tuple

def SQL_question_message(
        schema_info: str, 
        question: str, 
        feedback: str = None, 
        history: list[dict] = None
    ) -> list[dict]:
    """
    Construct a prompt message for LLM to generate a SQL query.

    Args:
        schema_info (str): A string representing the schema of a database. 
        question (str): The user's question.
        feedback (str): The feedback prompt to LLM.

    Returns:
        list[dict]: A list of message in a format for input to an LLM.
    """

    content = f"""
    Your task is to answer the question by generating a syntactically correct SQL query, given a database schema.
    Adhere to these rules:
    - **Deliberately go through the question and database schema word by word** to appropriately answer the question
    - **Use Table Aliases** to prevent ambiguity. For example, `SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.
    - When creating a ratio, always cast the numerator as float

    Input:
    Generate a SQL query that answers the user question: `{question}`.
    This query will run on a database whose schema is represented in the format:

    {schema_info}
    """

    if feedback is not None:
        content += f"""
    \nPrevious SQL queries generation failed, here is the feedback: {feedback} 
    Please take into consideration while generating response."""
        
    if history is None:
        messages = [
            {"role": "system", "content": """
    You are a helpful assistant for generating SQL queries.
    Pay attention to use only the column names that you can see in the schema description. 
    Pay attention to which column is in which table. 
    """
            }, 
            {"role": "user", "content": content}
        ]

        return messages
    # given history, add instruction
    else:
        return _chat_history(content, history)
        

def question_answer_message(
        question: str, 
        query: str, 
        result: list[Tuple], 
        history: list[dict] = None
    ) -> list[dict]:
    """
    Construct a prompt message for the LLM to generate answers based on the SQL query result.

    Args:
        question (str): The user's question.
        query (str): The SQL query obtained from LLM response.
        result (list[Tuple]): The result of the SQL query execution.

    Returns:
        list[dict]: A list of message in a format for input to an LLM.
    """
    RESULT_LIMIT = 20

    if len(result) > RESULT_LIMIT:
        result = f"{result[:RESULT_LIMIT]} etc, which has {len(result)} number of rows."

    content = f"""
    Given the following user question, corresponding SQL query,
    and SQL result, answer the user question directly. 

    SQL Query: {query}
    SQL Result: {result}
    User Question: {question}
    """

    if history is None:
        messages = [
            {"role": "system", "content": "You are a helpful assistant for answering questions given query result."}, 
            {"role": "user", "content": content}
        ]
        
        return messages
    else:
        return _chat_history(content, history)


def _chat_history(content, history):
    """
    Add chatting instruction for prompt and a LLM summarizer for context length exceeds limits
    """

    content += """
    Instructions:
    1. Refer to preivous response to provide contextually relevant answers.
    2. If a question or statement directly relates to something in the past, refer back to it explicitly.
    """
    
    history.append({"role": "user", "content": content})

    # TODO: Add a token checker and A LLM summarizer
    ...

    return history


# def func(messages):
#     """
#     TODO: A token checker and A LLM summarizer
#     """
#     ...

