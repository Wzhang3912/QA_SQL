from typing import Tuple
import tiktoken
from LLM import LLM_response
from utils import RESULT_LIMIT, INPUT_TOKEN_LIMIT

def SQL_question_message(
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
        Tuple(list[dict], list[dict]): A list of message in a format for input to an LLM.
    """

    content = f"""
    Your task is to answer the user question: `{question}`.
    If answering the user question requires retrieval from a database, then generated a syntactically correct SQL query to retrieve the answers, given the database schema.
    """

    if feedback is not None:
        content += f"""
    \nSQL queries generation failed, here is the feedback: {feedback} 
    Please take into consideration while generating response."""
    
    if history is None:
        messages = [
            {"role": "system", "content": """
    You are a helpful assistant for generating SQL queries.
    Adhere to these rules:
    - **Deliberately go through the question and database schema word by word** to appropriately answer the question.
    - **Use Table Aliases** to prevent ambiguity. For example, `SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.
    - When creating a ratio, always cast the numerator as float.
    - Pay attention to **use only the column names that you see in the schema description**.
    - Pay attention to **which column is in which table**."""}, 
            {"role": "user", "content": content}
        ]

        return messages
    # given history, add instruction
    else:
        return _chat_history(content, history, model_name)
        

def question_answer_message(
        question: str, 
        query: str, 
        result: list[Tuple], 
        history: list[dict] = None, 
        model_name: str = 'gpt-4o', 
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

    if len(result) > RESULT_LIMIT:
        result = str(result[:RESULT_LIMIT])[:-1] + f", ..., which has {len(result)} number of rows."

    content = f"""
    Given the following user question, corresponding SQL query,
    and SQL result, answer the user question directly. 

    SQL Query: {query}
    SQL Result: {result}
    User Question: {question}
    """

    return _chat_history(content, history, model_name)


def _chat_history(
        content: str, 
        history: list[dict], 
        model_name: str
    ) -> list[dict]:
    """
    Add chatting instruction for prompt  
    Summarize preivous conservation if length exceeds limits
    """

    content += """
    Instructions:
    1. Refer to preivous response to provide contextually relevant answers.
    2. If a question or statement directly relates to something in the past, refer back to it explicitly."""

    # Token checker and summarizer
    if count_tokens(history, model_name) > INPUT_TOKEN_LIMIT and len(history) > 5:

        # long term memory includes system prompt
        long_term_memory = history[0]
        # short term memory includes LLM response and user questions
        short_term_memory = history[1:]

        summary_question = {"role": "user", "content": "Summarize my previous conversation into a brief summary."}
        summary_response = {"role": "assistant", "content": summarizer(short_term_memory, model_name)}

        new_history = [long_term_memory]
        new_history.append(summary_question)
        new_history.append(summary_response)
        history = new_history

    history.append({"role": "user", "content": content})

    return history


def count_tokens(
        messages: list[dict], 
        model_name="gpt-4o-mini"
    ) -> int:
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


def word_count(messages: list[dict]) -> int:
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

