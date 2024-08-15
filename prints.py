import time
from datetime import datetime


# Print Assistants
def print_all_assistants(client):
    assistants = client.beta.assistants.list()
    for assistant in assistants.data:
        human_time = datetime.fromtimestamp(assistant.created_at).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        print(
            f"ID: {assistant.id}\n",
            f"Name: {assistant.name}\n",
            f"Description: {assistant.description}\n",
            f"Model: {assistant.model}\n",
            # f"Instructions: {assistant.instructions}\n",
            f"Tools: {assistant.tools}\n",
            f"Created At: {human_time}\n",
        )


def print_assistant(assistant):
    human_time = datetime.fromtimestamp(assistant.created_at).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    print(
        f"ID: {assistant.id}, Name: {assistant.name}, Model: {assistant.model}\n",
        # f"Description: {assistant.description}\n",
        # f"Instructions: {assistant.instructions}\n",
        f"Tools: {assistant.tools}\n",
        f"Tool Resources: {assistant.tool_resources}\n",
        f"Created At: {human_time}\n",
    )


# Print Threads
def print_all_threads():
    ...
    return None


def print_thread(thread):
    human_time = datetime.fromtimestamp(thread.created_at).strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"ID: {thread.id}\n",
        f"Tool Resources: {thread.tool_resources}\n",
        # f"Metadata: {thread.metadata}\n",
        f"Created At: {human_time}\n",
    )


# Print Messages
def print_all_messages(client, thread_id):
    try:
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        message_counter = 0
        for message in messages.data:
            print(
                f"Message {message_counter} ---> Role: {message.role}, ID: {message.id}"
            )
            print(message.content[0].text.value, "\n")
            message_counter += 1
    except Exception:
        print("No messages")
    print(f"--- Total Messages: {message_counter} ---\n")


def print_last_message(client, thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    last_message = messages.data[-1]
    print(last_message.content[0].text.value)


# Print Runs
def print_all_runs(client, thread_id):
    runs = client.beta.threads.runs.list(thread_id=thread_id)
    for run in runs.data:
        print(
            f"Run ID: {run.id}, Status: {run.status}, Assistant ID: {run.assistant_id}"
        )


# Print Steps
def print_run_steps(client, thread_id, run_id):

    run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run_id)

    for step in run_steps.data:
        step_counter = 0
        while True:
            if step.completed_at:
                print(f"Total Steps: {step_counter}")
                print(
                    f"Step {step_counter} ---> ID: {step.id}, Type: {step.type}, Status: {step.status}"
                )
                step_counter += 1
                break
            else:
                print(f"Step ---> ID: {step.id}, Status: {step.status}")
            time.sleep(5)


# Print Response
def print_response(client, thread_id):
    while True:
        time.sleep(2)
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            try:
                message.role == "assistant"
                response = message.content[0].text.value
                print(f"Assistant: {response}")
                break
            except Exception:
                print("No response from the assistant.")
        break


def list_files(client):
    files_list = []
    if not client.files.list().data:
        print("No files found.")
        return

    files = client.files.list()
    for counter, file in enumerate(files.data, start=1):
        file_info = {
            "id": file.id,
            "filename": file.filename,
            "purpose": file.purpose,
            "bytes": file.bytes,
            "status": file.status,
        }
        files_list.append(file_info)
    print(
        f"\nTotal Files: {len(files_list)}",
        "-" * (100 - (len("Total Files:  ") + len(str(len(files_list))))),
        "\n"
        + f'{"No.":<5}{"ID":<32}{"Filename":<26}{"Size":<7}{"":<7}{"Purpose":<14}{"Status":<8}',
        "\n" + "-" * 100,
    )

    for i, file_info in enumerate(files_list):
        # Convert bytes to MB for proper display
        size_mb = file_info["bytes"] / (1024 * 1024)  # Convert bytes to MB
        print(
            f"{i + 1:<5}{file_info['id']:<32}{file_info['filename']:<26}"
            + f"{size_mb:<7.2f}{"MB":<7}{file_info['purpose']:<14}{file_info['status']:<8}"
        )

    print("")
    return files_list


def list_vector_stores(client):
    vector_stores = client.beta.vector_stores.list()
    for vector_store in vector_stores.data:
        print(f"ID: {vector_store.id}\n")
        return vector_store


def list_vector_store_files(client, vector_store_id):
    vector_store_files = client.beta.vector_stores.files.list(
        vector_store_id=vector_store_id
    )
    vector_store_files_ids = []
    for vector_store_file in vector_store_files.data:
        vector_store_files_ids.append(vector_store_file.id)
        print(
            f"ID: {vector_store_file.id}, bytes: {vector_store_file.usage_bytes}, status: {vector_store_file.status}\n"
        )
    return vector_store_files_ids
