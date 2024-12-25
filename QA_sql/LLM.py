import requests
from openai import OpenAI
import time
import os
import json

def LLM_response(
        messages: list[dict], 
        model_name: str, 
        stream: bool = True, 
        url: str = "http://localhost:11434/api/generate"
    ) -> str:
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
           raise ValueError('OPEN AI API key not found')
        
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
                            chunk = json.loads(line.decode('utf-8'))
                            # yield the result as they come in
                            yield chunk.get("response", "")

                            if chunk.get("done", False):
                                break
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


def GPT_response(
        messages: str, 
        model_name: str, 
        stream: bool = True, 
        api_key: str = None
    ) -> str:
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
                stream=True,
            )

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

