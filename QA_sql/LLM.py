import requests
# import instructor
# from pydantic import ValidationError
from openai import OpenAI
import time
import os
import json

def LLM_response(messages, model_name, stream=True, url="http://localhost:11434/api/generate"):
    """
    Fetch responses from LLM

    Args:
        messages (list[dict]): list of message dictionaries following ChatCompletion format
        model_name (str): name of the LLM model
        url (str): endpoint where LLM is hosted
    Returns:
        str: The LLM output.
    """
    
    if model_name[:3].lower() == 'gpt':
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key is None:
           raise ValueError('OPEN AI api key not found')
        
        # uncomment the code below, put api key here if you don't want to set up os environment variable
        # api_key = 'REPLACE YOUR OPENAI API KEY HERE'

        response = GPT_response(messages, model_name, stream=stream, api_key=api_key)
        
        return response
    
    prompt = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages]
    )
    data = {
        "model": model_name,
        "prompt": prompt,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stream": stream,
    }

    def _stream_response(data, url):
        try:
            # LLM streaming
            print('Streaming')
            response = requests.post(url=url, json=data, stream=True)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            # Parse JSON response
                            chunk = json.loads(line.decode('utf-8'))
                            yield chunk.get("response", "")

                            if chunk.get("done", False):
                                break  # done streaming
                        except json.JSONDecodeError:
                            continue
            else:
                print("Error:", response.status_code, response.json())
                return None

        except Exception as e:
            print(f"API call failed: {e}")
            return None

    def _response(data, url):
        try:
            response = requests.post(url=url, json=data)
            if response.status_code == 200:
                response_text = response.json().get("response", "")
                return response_text
            else:
                print("Error:", response.status_code, response.json())
                return None

        except Exception as e:
            print(f"API call failed: {e}")
            return None
        
    if stream:
        return _stream_response(data, url)
    else:
        return _response(data, url)


def GPT_response(messages, model_name, stream=True, api_key=None):
    """
    Fetch response from openai LLM model

    Args:
        messages (str): raw messages
        model_name (str): name of the openai model
        api_key (str): the api key to access openai model
    Returns:
        str: The openai LLM output.
    """
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY')

    client = OpenAI(api_key=api_key)

    def _stream_response(client, messages, model_name):
        print('Streaming')
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stream=True,
            )
            # yield the parts of the response as they come
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"API call failed: {e}")
            return None

    def _response(client, messages, model_name):
        try:
            result = client.chat.completions.create(
                model=model_name,
                messages=messages,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stream=stream,
            )
            return result.choices[0].message.content

        except Exception as e:
            print(f"API call failed: {e}")
            return None
    
    if stream:
        return _stream_response(client, messages, model_name)
    else:
        return _response(client, messages, model_name)


# def LLaMA_response_json(
#     messages, model_name, response_model, api_key='ollama', url="http://localhost:11434/v1"
# ):
#     """
#     LLM module to be called

#     Args
#         messages: list of message dictionaries following ChatCompletion format
#         model_name: name of the LLaMA model
#         url: endpoint where LLaMA is hosted
#     """
#     MAX_RETRY = 7
#     count = 0

#     if model_name[:3] == 'gpt':
#         api_key = os.getenv('OPENAI_API_KEY')
#         if api_key is None:
#             raise ValueError('OPEN AI api key not found')
    
#     # enables `response_model` in create call
#     try:
#         if api_key == 'ollama':
#             client = OpenAI(
#                 base_url=url,
#                 api_key=api_key, 
#             )
#         # OPEN AI model
#         else:
#             client = OpenAI(api_key=api_key)

#         client = instructor.from_openai(
#             client, 
#             mode=instructor.Mode.JSON,
#             # temperature=0.3,
#         )
#         while True:
#             if count >= MAX_RETRY:
#                 print(
#                     f"""Max retries reach. LLM failed at outputing the correct result. 
#                 Input parameter response_model might have issue: {response_model.schema_json(indent=2)}"""
#                 )
#                 raise ValidationError
#             try:
#                 # Use instructor to handle the structured response
#                 response = client.chat.completions.create(
#                     model=model_name,
#                     messages=messages,
#                     response_model=response_model,  # Use the Character model to structure the response
#                 )
#                 # Print the structured output as JSON
#                 response = response.model_dump_json()
#                 token_num_count = sum(
#                     len(enc.encode(msg["content"])) for msg in messages
#                 ) + len(enc.encode(response))
#                 return response, token_num_count
#             except Exception as e:
#                 count += 1
#                 print(
#                     f"Validation failed during LLM output generation: {e} for {count} times. Retrying..."
#                 )
#     except Exception as e:
#         print(f"API call failed: {e}")
#         return None, 0

