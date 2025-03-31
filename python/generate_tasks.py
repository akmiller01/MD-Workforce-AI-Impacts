import pandas as pd
import os
from pydantic import BaseModel
import google
from google import genai
import time
import json
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from tqdm import tqdm
import argparse

GEMINI_TASK_SYSTEM_PROMPT = (
    "For the cross-industry occupation title below, please enumerate a full list of reasonable tasks that a person "
    "in that occupation would need to perform on a daily basis. Consider the entire spectrum of that individual's "
    "duties and responsibilities, both online (if applicable) and in person, in formulating the tasks. "
    "Please respond only with valid JSON in the specified format.\nThe occupation title is:\n{}"
)

GPT_TASK_SYSTEM_PROMPT = (
    "For the cross-industry occupation title given by the user, please enumerate a full list of reasonable tasks that a person "
    "in that occupation would need to perform on a daily basis. Consider the entire spectrum of that individual's "
    "duties and responsibilities, both online (if applicable) and in person, in formulating the tasks. "
    "Please respond only with valid JSON in the specified format."
)


class EnumeratedDuties(BaseModel):
    tasks: list[str]


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


def main():
    parser = argparse.ArgumentParser(
                    prog='Generate occupation tasks',
                    description='Generate occupation tasks')
    parser.add_argument('-m', '--model', default='gemini')
    args = parser.parse_args()

    load_dotenv()
    if args.model == 'gemini':
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if GEMINI_API_KEY is None:
            print("Please provide a GEMINI_API_KEY in a .env file.")
            return
        client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if OPENAI_API_KEY is None:
            print("Please provide an OPENAI_API_KEY in a .env file.")
            return
        client = OpenAI(api_key = OPENAI_API_KEY)

    input_occupation_df = pd.read_csv('../input/all_occupation_titles.csv')
    input_occupations = input_occupation_df['occupation_title'].values.tolist()
    output_records = list()
    for input_occupation in tqdm(input_occupations):
        if args.model == 'gemini':
            query_contents = GEMINI_TASK_SYSTEM_PROMPT.format(input_occupation)
            llm_response_json = query_gemini(client, query_contents, EnumeratedDuties)
        else:
            query_contents = [
                {
                    'role': 'system',
                    'content': GPT_TASK_SYSTEM_PROMPT,
                },
                {
                    'role': 'user',
                    'content': input_occupation,
                },
            ]
            llm_response_json = query_gpt(client, query_contents, EnumeratedDuties)
        for task in llm_response_json['tasks']:
            output_dict = {
                'occupation_title': input_occupation,
                'task': task
            }
            output_records.append(output_dict)
    
    df = pd.DataFrame.from_records(output_records)

    csv_filepath = "../input/all_occupation_tasks.csv"
    df.to_csv(csv_filepath, index=False)
    print(f"Data saved to {csv_filepath}")

if __name__ == '__main__':
    main()
