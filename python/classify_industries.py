import pandas as pd
import os
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import argparse
from typing import Literal
from common import query_gemini, query_gpt


lighthouse_industries = [
    'Aerospace and Defense',
    'Artificial Intelligence',
    'Bio-tech',
    'Clean Energy',
    'Life Sciences',
    'Quantum Computing',
    'Information Technology',
    'None of the above'
]

GEMINI_SYSTEM_PROMPT = (
    "For the cross-industry occupation title below, classify it into the industry category it most closely fits into. "
    "The industry categories are:\n{}\n"
    "If the occupation title does not closely fit into any of the categories, choose 'None of the above'. "
    "Please respond only with valid JSON in the specified format.\nThe occupation title is:\n{{}}"
)
GEMINI_SYSTEM_PROMPT = GEMINI_SYSTEM_PROMPT.format(
    "\n".join([f'- {value}' for value in lighthouse_industries]),
)

GPT_SYSTEM_PROMPT = (
    "For the cross-industry occupation title given by the user, classify it into the industry category it most closely fits into. "
    "The industry categories are:\n{}\n"
    "If the occupation title does not closely fit into any of the categories, choose 'None of the above'. "
    "Please respond only with valid JSON in the specified format."
)
GPT_SYSTEM_PROMPT = GPT_SYSTEM_PROMPT.format(
    "\n".join([f'- {value}' for value in lighthouse_industries]),
)

class Classification(BaseModel):
    classification: Literal[tuple(lighthouse_industries)]


def main():
    parser = argparse.ArgumentParser(
                    prog='Classify occupations into lighthouse industries',
                    description='Classify occupations into lighthouse industries')
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
            query_contents = GEMINI_SYSTEM_PROMPT.format(input_occupation)
            llm_response_json = query_gemini(client, query_contents, Classification)
        else:
            query_contents = [
                {
                    'role': 'system',
                    'content': GPT_SYSTEM_PROMPT,
                },
                {
                    'role': 'user',
                    'content': input_occupation,
                },
            ]
            llm_response_json = query_gpt(client, query_contents, Classification)
        output_dict = {
            'occupation_title': input_occupation,
            'industry_classification': llm_response_json['classification']
        }
        output_records.append(output_dict)
    
    df = pd.DataFrame.from_records(output_records)

    csv_filepath = "../input/all_occupation_titles_industry.csv"
    df.to_csv(csv_filepath, index=False)
    print(f"Data saved to {csv_filepath}")

if __name__ == '__main__':
    main()
