import os
import time

from dotenv import load_dotenv
from openai import OpenAI

import prints
import utils
from utils import cold_start

load_dotenv()

# openai.api_key = os.environ.get("OPENAI_API_KEY")
# defaults to getting the key using os.environ.get("OPENAI_API_KEY")
# if you saved the key under a different environment variable name, you can do something like:
# client = OpenAI(
#   api_key=os.environ.get("CUSTOM_ENV_NAME"),
# )

ASSISTANT_ID = os.environ.get("ASSISTANT_ID")
THREAD_ID = os.environ.get("THREAD_ID")
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID")

client = OpenAI()
models = ["gpt-3.5-turbo", "gpt-3.5-turbo-0125", "gpt-4o", "gpt-4o-mini"]
model = "gpt-4o"

assistant_id = ASSISTANT_ID
thread_id = THREAD_ID
vector_store_id = VECTOR_STORE_ID

try:
    with open("instructions.txt", "r") as file:
        instructions = file.read()
except FileNotFoundError:
    print("Instructions file NOT found!")


# Assistant
# utils.update_assistant(client, assistant_id, instructions, model)
# while True:
#     try:
#         assistant = client.beta.assistants.retrieve(assistant_id)
#     except Exception:
#         print("Assistant NOT found! You need to CREATE A NEW ASSISTANT.")
#         assistant_name = input("Enter assistant name: ").strip()
#         print("\nMake sure you've filled and saved the instructions.txt file!")
#         input("Press Enter to continue ...")
#         print("\nModels available:")
#         print("-----------------")
#         count = 0
#         for model in models:
#             print(f"{count} : {model}")
#             count += 1

#         while True:
#             model_or_name = input(
#                 f"\nEnter a number between 0 and {count} to select one of the above models, "
#                 "or you can type the name of the model: "
#             )
#             try:
#                 model = models[int(model_or_name)]
#             except ValueError:
#                 model = model_or_name
#                 assistant = utils.create_assistant(
#                     client, instructions, assistant_name, model
#                 )
#             except Exception:
#                 model = "gpt-4o-mini"
#                 print("Model NOT found! Defaulting to gpt-4o-mini.")
#                 assistant = utils.create_assistant(
#                     client, instructions, assistant_name, model
#                 )
#                 continue
#             else:
#                 assistant = utils.create_assistant(
#                     client, instructions, assistant_name, model
#                 )
#             finally:
#                 print("Creating assistant...")
#                 break
#         continue
#     else:
#         print("Assistant retrieved.")
#     finally:
#         # prints.print_assistant(assistant)
#         pass

assistant = utils.retrieve_or_create_assistant(
    client, assistant_id, models, instructions
)

exit()

# Thread
thread_id = "thread_aYzTO4PfioO55eDNPaHWX3l4"

try:
    thread = client.beta.threads.retrieve(thread_id)
except Exception:
    print("Thread NOT found!\nCreate a NEW THREAD.")
    # thread = client.beta.threads.create()
finally:
    prints.print_thread(thread)
    pass


# Vector Store
vector_store_id = "vs_pp231m0pBjMuD0gC0NOOyONM"

try:
    vector_store = client.beta.vector_stores.retrieve(vector_store_id)
    print("Vector Store retrieved.")
except Exception:
    print("Vector Store NOT found!\nCreate a NEW VECTOR STORE.")
    exit()
finally:
    prints.list_vector_stores(client)
    pass

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
content = "Where to collect data for large language models? Answer in a sentence."

cold_start(client, thread_id)

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
