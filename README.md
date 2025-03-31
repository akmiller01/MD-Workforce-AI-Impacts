# MD-Workforce-AI-Impacts
A preliminary investigation into how AI might affect Maryland's workforce along ACS occupation codes

## Installation (windows)
```
cd python
python -m virtualenv venv
cd venv/Scripts
activate
cd ../..
pip install -r requirements.txt
```

Copy `python/.env-example` to `python/.env` and fill in the requisite API keys.

## Running Python inference
```
python generate_tasks.py -m gpt
python rate_tasks.py -m gpt
```