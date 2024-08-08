import os

# import sys
import time
from typing import Final

from dotenv import load_dotenv
from openai import OpenAI

import prints
import utils

# Load environment variables
while True:
    try:
        load_dotenv(override=True)
        OPENAI_API_KEY: Final = os.environ.get("OPENAI_API_KEY")
        client = OpenAI(api_key=OPENAI_API_KEY)
        models_object = client.models.list()
        break
    except Exception as e:
        print(f"Error: {str(e)}\n")
        api_key = input("Please enter your OpenAI API Key: ").strip()
        utils.update_environment(api_key=api_key)
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

thread = utils.retrieve_or_create_thread(client, thread_id)

vector_store = utils.retrieve_or_create_vector_store(client, vector_store_id)

# Update Environment
utils.update_environment(
    path=".env",
    api_key=OPENAI_API_KEY,
    assistant_id=assistant.id,
    thread_id=thread.id,
    vector_store_id=vector_store.id,
)

# File Handling
files_list = prints.list_files(client)

while True:
    yes_or_no = (
        input(
            "If you want to upload a new file(s): Enter 'y' ,\n"
            "If you want to continue with existing files: Enter 'n' ,\n"
            "If you want to start with no files, then: Enter 'z' :\n\n"
        )
        .strip()
        .lower()
    )

    if yes_or_no in ["exit", "quit", "q", "bye"]:
        break

    elif yes_or_no in ["y", "yes", "yeap"]:
        try:
            utils.delete_files(client, files_list)
        except Exception:
            print("No files to delete.")

        while True:
            file_name = input(
                "\nEnter file name (including file extension) or enter 'q' to see file options :\n"
            ).strip()

            if file_name.lower() in ["exit", "quit", "q", "bye"]:
                break
            else:
                try:
                    file = utils.upload_file(client, file_name)
                    files_list = prints.list_files(client)
                    if file:
                        print(f"ID {file}: File uploaded.")
                except Exception as e:
                    print(
                        f"File NOT uploaded. Error: {str(e)}\n"
                        "Please enter a valid file name (including file extension) :"
                    )

    elif yes_or_no in ["n", "no", "nope"]:
        print("Starting with files below:\n")
        break
    elif yes_or_no in ["0", "z", "zero"]:
        utils.delete_files(client, files_list)
        break
    else:
        print("\nInvalid input! These are the options:\n")

# List vector store files again
files_list = prints.list_files(client)

utils.create_vs_file(client, files_list, vector_store_id)


# Fresh Start
utils.cold_start(client, thread_id)

print(
    f"Assistant ID: {assistant_id}\nThread ID: {thread_id}\nVector Store ID: {vector_store_id}\n"
)

# Chat
while True:
    text = input("\nUser: ")
    if text.lower() in ["exit", "quit", "q", "bye"]:
        print("Sorry to see you go!")
        break
    else:
        pass

    utils.create_message(client, text, thread_id)

    run = utils.create_run(client, assistant_id, thread_id)
    while not run.completed_at:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        # print(run.status)
        time.sleep(1)

    prints.print_response(thread_id)

#     utils.print_run_steps(thread_id, run.id)

# utils.print_all_messages(thread_id)
