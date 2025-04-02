import pandas as pd
import os
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import argparse
from common import query_gemini, query_gpt

GEMINI_TASK_SYSTEM_PROMPT = (
    "For the cross-industry occupation title and specific task below, rate the task's exposure to AI automation from 1-5. "
    "The ratings have the following interpretations:\n"
    "- 1: AI cannot perform the task at all\n"
    "- 2: AI can perform the task with assistance from a human operator\n"
    "- 3: AI can perform the task as well as an average human\n"
    "- 4: AI can perform the task as well as an expert human\n"
    "- 5: AI can perform the task better than an expert human\n"
    "Consider the entire spectrum of that occupation's duties and responsibilities, both online (if applicable) and in person, in formulating the ratings. "
    "Also consider the legal, physical, and emotional requirements of the task. Most tasks that require a physical presence should be rated 1. "
    "Please respond only with valid JSON in the specified format.\nThe occupation title and task are:\n{} - {}"
)

GPT_TASK_SYSTEM_PROMPT = (
    "For the cross-industry occupation title and specific task given by the user, rate the task's exposure to AI automation from 1-5. "
    "The ratings have the following interpretations:\n"
    "- 1: AI cannot perform the task at all\n"
    "- 2: AI can perform the task with assistance from a human operator\n"
    "- 3: AI can perform the task as well as an average human\n"
    "- 4: AI can perform the task as well as an expert human\n"
    "- 5: AI can perform the task better than an expert human\n"
    "Consider the entire spectrum of that occupation's duties and responsibilities, both online (if applicable) and in person, in formulating the ratings. "
    "Also consider the legal, physical, and emotional requirements of the task. Most tasks that require a physical presence should be rated 1. "
    "Please respond only with valid JSON in the specified format."
)


class TaskRating(BaseModel):
    rating: int


def main():
    parser = argparse.ArgumentParser(
                    prog='Rate occupation tasks',
                    description='Rate occupation tasks')
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

    input_occupation_df = pd.read_csv('../input/all_occupation_tasks.csv')
    input_occupation_df = input_occupation_df.reset_index()
    output_records = list()
    total_iterations = len(input_occupation_df)
    with tqdm(total=total_iterations, desc="Processing") as pbar:
        for index, row in input_occupation_df.iterrows():
            input_occupation = row['occupation_title']
            task = row['task']
            if args.model == 'gemini':
                query_contents = GEMINI_TASK_SYSTEM_PROMPT.format(input_occupation, task)
                llm_response_json = query_gemini(client, query_contents, TaskRating)
            else:
                query_contents = [
                    {
                        'role': 'system',
                        'content': GPT_TASK_SYSTEM_PROMPT,
                    },
                    {
                        'role': 'user',
                        'content': f"{input_occupation} - {task}",
                    },
                ]
                llm_response_json = query_gpt(client, query_contents, TaskRating)
            output_dict = {
                'occupation_title': input_occupation,
                'task': task,
                'rating': llm_response_json['rating']
            }
            output_records.append(output_dict)
            pbar.update(1)
    
    df = pd.DataFrame.from_records(output_records)

    csv_filepath = "../output/all_occupation_task_ratings.csv"
    df.to_csv(csv_filepath, index=False)
    print(f"Data saved to {csv_filepath}")

if __name__ == '__main__':
    main()
