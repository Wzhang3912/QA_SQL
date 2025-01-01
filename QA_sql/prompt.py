from typing import Tuple
import tiktoken
from LLM import LLM_response

def SQL_question_message(
        schema_info: str, 
        question: str, 
        feedback: str = None, 
        history: list[dict] = None, 
        model_name: str = 'gpt-4o'
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

    {schema_info}"""

    if feedback is not None:
        content += f"""
    \nSQL queries generation failed, here is the feedback: {feedback} 
    Please take into consideration while generating response."""
    
    if history is None:
        messages = [
            {"role": "system", "content": """
    You are a helpful assistant for generating SQL queries.
    Adhere to these rules:
    - **Deliberately go through the question and database schema word by word** to appropriately answer the question
    - **Use Table Aliases** to prevent ambiguity. For example, `SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.
    - When creating a ratio, always cast the numerator as float
    - Pay attention to use only the column names that you can see in the schema description. 
    - Pay attention to which column is in which table."""
            }, 
            {"role": "user", "content": content}
        ]

        return messages
    # given history, add instruction
    else:
        content = f"""
    Your task is to answer the user question {question}.
    If the Generated a syntactically correct SQL query if necessary to answer the user question."""
        return _chat_history(content, history, model_name)
        

def question_answer_message(
        question: str, 
        query: str, 
        result: list[Tuple], 
        history: list[dict] = None, 
        model_name: str = 'gpt-4o'
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
    print(history)
    if history is None:
        messages = [
            {"role": "system", "content": "You are a helpful assistant for answering user questions."}, 
            {"role": "user", "content": content}
        ]
        
        return messages
    else:
        print(1)
        return _chat_history(content, history, model_name)


def _chat_history(content, history, model_name):
    """
    Add chatting instruction for prompt  
    Summarize preivous conservation if length exceeds limits
    """

    content += """
    Instructions:
    1. Refer to preivous response to provide contextually relevant answers.
    2. If a question or statement directly relates to something in the past, refer back to it explicitly."""

    INPUT_TOKEN_LIMIT = 16384

    # Token checker and summarizer
    if count_tokens(history, model_name) > INPUT_TOKEN_LIMIT and len(history) > 5:
        print('Summarizing')
        print(f'BEFORE TOKEN: {count_tokens(history, model_name)}')
        # long term memory includes system prompt and schema infomation
        long_term_memory = history[:2]
        # short term memory includes LLM response and user questions
        short_term_memory = history[2:]

        summary_question = {"role": "user", "content": "Summarize my previous conversation into a brief summary."}
        summary_response = {"role": "assistant", "content": summarizer(short_term_memory, model_name)}
        
        long_term_memory.append(summary_question)
        long_term_memory.append(summary_response)
        history = long_term_memory
        print(summary_response)

    history.append({"role": "user", "content": content})
    print(history)
    print(f'AFTER TOKEN: {count_tokens(history, model_name)}')

    return history


def count_tokens(messages, model_name="gpt-4o-mini"):
    """
    Count number of tokens in messages prompt for OpenAI model.

    Args:
        messages (list[dict]): The conversation messages.
        model_name (str): The name of the GPT model.

    Returns:
        int: The total number of tokens in the messages.
    """
    if model_name[:3].lower() == 'gpt':
        try:
            encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # default tokenizer
            encoding = tiktoken.get_encoding("cl100k_base")

        token_count = 0
        for message in messages:
            token_count += len(encoding.encode(message["role"]))
            token_count += len(encoding.encode(message["content"]))
            # structural tokens 
            token_count += 2 

        # for general structure token
        token_count += 3

        return token_count
    
    else:
        return word_count(messages)


def word_count(messages):
    """
    Count the number of words in messages prompt
    Alternative to token counter, give an estimate of the number of tokens when model tokenizer is unknown

    Args:
        messages (list[dict]): The conversation messages.

    Returns:
        int: Estimated number of tokens based on word count.
    """
    # a heuristic estimation correction
    TOKEN_CORRECTION = 4/3

    word_count = 0
    for message in messages:
        content = f"{message['role']}: {message['content']}"
        word_count += len(content.split()) 
    return word_count * TOKEN_CORRECTION


def summarizer(messages: list[dict], model_name: str) -> str:
    """
    Summarize preivous conservation messages using LLM

    Args:
        messages (ist[dict]): 
        model_name: The model name to use in summarizer
    """

    summary_messages = [
        {"role": "system", "content": "You are an assistant that summarizes conversations."},
        *messages,
        {"role": "user", "content": "Summarize all previous conversation. Try to include all important user questions and assistant response."}
    ]
    
    response = LLM_response(summary_messages, model_name, stream=False)

    return response

