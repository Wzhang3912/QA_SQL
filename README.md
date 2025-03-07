# QA_SQL
An LLM-driven SQL questions-answering tool for PostgreSQL database. 

## Demos
- Click `Generate Response` for generating a response that contains SQL query
- Click `Extract & Execute SQL` for extracting SQL query from response, executing query and displaying the results. 

![Demos Example 1](assets/videos/demos_1.gif)

- Click `Generate Answer` for generating a answer to the question, given the result retrieved from the database.

![Demos Example 2](assets/videos/demos_2.gif)

## Set Up

### Install

Install the necessary dependencies for connecting with the PostgreSQL database and using the OpenAI Large Language Model:

```bash
pip install openai psycopg2-binary tiktoken
```

### LLM set up

The application supports both locally hosted models and OpenAI models.

- Download ollama for hosting LLM locally: [here](https://ollama.com/download)
- Register your OpenAI API Key for using OpenAI model: [here](https://platform.openai.com/docs/api-reference/introduction)
    - Put your API key in the `QA_sql/configs/config.conf` file.

### Run

Run the following Python script to open the interactive UI application:

```bash
python QA_sql/run.py --model_name MODEL_NAME --database_name DATABASE_NAME
```

Replace `MODEL_NAME` with your choice of LLM model and `DATABASE_NAME` with your database name. 

