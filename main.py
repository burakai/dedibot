import os

# import sys
from typing import Final

from dotenv import load_dotenv
from openai import OpenAI

import prints
import utils

setup = input(
    "Choose one of the options below and press 'Enter':\n\n"
    "[0] Start from zero    \n"
    + "[1] Load defaults (recents)   \n"
    + "[2] Load defaults and messages    \n"
    + "[3] Edit files and load defaults   \n"
    + "[4] Change defaults [Advanced] \n"
)

env_path = ".env"
utils.check_env(env_path)

# Load environment variables
while True:
    try:
        load_dotenv(env_path, override=True)
        OPENAI_API_KEY: Final = os.environ.get("OPENAI_API_KEY")
        client = OpenAI(api_key=OPENAI_API_KEY)
        models_object = client.models.list()
        break
    except Exception as e:
        print(f"Error: {str(e)}\n")
        api_key = input("Please enter your OpenAI API Key: ").strip()
        utils.update_env(api_key=api_key)
        continue

models: dict[str] = utils.create_models_dict(models_object)

ASSISTANT_ID: Final = os.environ.get("ASSISTANT_ID")
THREAD_ID: Final = os.environ.get("THREAD_ID")
VECTOR_STORE_ID: Final = os.environ.get("VECTOR_STORE_ID")
DEFAULT_MODEL: Final = os.environ.get("DEFAULT_MODEL")

assistant_id = ASSISTANT_ID
thread_id = THREAD_ID
vector_store_id = VECTOR_STORE_ID
default_model = DEFAULT_MODEL

# Read Instructions
instructions = utils.instructions_from_file()

# Assistant, Thread and Vector Store
assistant = utils.retrieve_or_create_assistant(
    client, assistant_id, models, default_model, instructions
)

vector_store = utils.retrieve_or_create_vector_store(client, vector_store_id)

thread = utils.retrieve_or_create_thread(client, thread_id)

# Update Environment
utils.update_env(
    path=env_path,
    api_key=OPENAI_API_KEY,
    assistant_id=assistant.id,
    thread_id=thread.id,
    vector_store_id=vector_store.id,
    default_model=assistant.model,
)

# File Handling
files_list = prints.list_files(client)

file_batch = utils.upload_file_batch(client, vector_store)


# assistant = client.beta.assistants.update(
#     assistant_id=assistant.id,
#     tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
# )

assistant = utils.update_assistant(
    client, assistant.id, vector_store.id, instructions, default_model
)

# List vector store files again
files_list = prints.list_files(client)

# Create VS File
# utils.create_vs_file(client, files_list, vector_store.id)


# # Fresh Start
utils.cold_start(client, thread.id)

# # Chat
utils.chat(client, assistant.id, thread.id)
