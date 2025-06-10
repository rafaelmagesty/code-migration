# code-migration
Studying the ability of public LLMs to migrate code between two equivalent libraries.

## Instructions

### 1. Create and Activate Venv
`python3 -m venv venv`

`source venv/bin/activate`

### 2. Install Dependencies
`pip install -r requirements.txt`

Remember to update the requirements when installing a new lib:

`pip freeze > requirements.txt`

### 3. Generate Input Examples
First, make sure the migrations dataset is available inside the input folder, then run:

`python3 generate_examples.py path_to_df`

If you want to use your own df, please insert it in input/programming_language to keep code consistency. Remember to add your new example dir inside the gitignore.

### 3. Usage
Understand better in:

`python3 main.py --help`

Or try your luck with:

usage: main.py <LANGUAGE_NAME> <OLD_LIB_NAME> <NEW_LIB_NAME> <MODEL> <VERSION> <PROMPT>