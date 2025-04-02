import google
import time
import json
from openai import OpenAIError


def query_gemini(client, contents, response_format):
    time.sleep(4) # Free tier rate limit of 15 per minute
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                # model='gemini-2.5-pro-exp-03-25',
                model = 'gemini-2.0-flash',
                contents=contents,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': response_format,
                },
            )
            json_response = json.loads(response.text)
            return json_response
        except google.genai.errors.ServerError as e:
            print(f"Connection error: {e}")
            if attempt < max_retries - 1:
                sleep_duration = (2 ** attempt) * 1
                print(f"Retrying in {sleep_duration} seconds...")
                time.sleep(sleep_duration)
            else:
                print("Max retries reached.  Returning None.")
                return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response.text}")
            if attempt < max_retries - 1:
                sleep_duration = (2 ** attempt) * 1
                print(f"Retrying in {sleep_duration} seconds...")
                time.sleep(sleep_duration)
            else:
                print("Max retries reached.  Returning None.")
                return None
    return None

def query_gpt(client, contents, response_format):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            completion = client.beta.chat.completions.parse(
                model='gpt-4o-mini',
                messages=contents,
                response_format=response_format
            )
            json_response = completion.choices[0].message.parsed
            return json_response.model_dump()
        except OpenAIError as e:
            print(f"Connection error: {e}")
            if attempt < max_retries - 1:
                sleep_duration = (2 ** attempt) * 1
                print(f"Retrying in {sleep_duration} seconds...")
                time.sleep(sleep_duration)
            else:
                print("Max retries reached.  Returning None.")
                return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response.text}")
            if attempt < max_retries - 1:
                sleep_duration = (2 ** attempt) * 1
                print(f"Retrying in {sleep_duration} seconds...")
                time.sleep(sleep_duration)
            else:
                print("Max retries reached.  Returning None.")
                return None
    return None