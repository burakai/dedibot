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

client = OpenAI()
model = "gpt-4o"

instructions = """You are a helpful document expert. You always answer in Turkish.
        When asked a question, explain the answer using the information from the document you have access to.
        Ensure your response is clear, concise, and directly relevant to the content of the document.
        If the document does not contain the necessary information, politely inform the user
        and don't suggest any next steps or additional sources that might be helpful.
        Instead, indicate this in your answer and do NOT answer the question.
        If you don't know the answer, you should simply say something like 'I'm sorry, but I don't know the answer'."""

# Assistant
assistant_id = "asst_fx4XZaTQcmidmhUYZY23XSmg"
# utils.update_assistant(client, assistant_id, instructions, model)

try:
    assistant = client.beta.assistants.retrieve(assistant_id)
except Exception:
    print("Assistant NOT found!\nCreate a NEW ASSISTANT.")
    # assistant = utils.create_assistant(client, instructions, "Document Expert", model)
finally:
    prints.print_assistant(assistant)
    pass


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
