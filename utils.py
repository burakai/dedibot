import time
from datetime import datetime

import prints


# # Decorators
def print_created(f):
    def wrapper(*args, **kwargs):
        print(f"\n{f.__name__} created!\n")
        return f(*args, **kwargs)

    return wrapper


def timer(f):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print(f"\n{f.__name__} took {end - start} seconds.\n")
        return result

    return wrapper


# # Fresh Start
def delete_all_messages(client, thread_id) -> None:
    print("Deleting all messages...\n")
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    if not messages.data:
        print("No messages to delete.\n")
        return
    for message in messages.data:
        client.beta.threads.messages.delete(thread_id=thread_id, message_id=message.id)
        print(f"{message.id} - {message.role} message deleted.")
    return None


def cold_start(client, thread_id) -> None:
    delete_all_messages(client, thread_id)
    time.sleep(1)
    print("Cold start!\n")
    prints.print_all_messages(thread_id)
    return None


# # Models
def update_environment(
    path: str = ".env",
    api_key: str = None,
    assistant_id: str = None,
    thread_id: str = None,
    vector_store_id: str = None,
) -> None:
    with open(path, "r") as file:
        lines = file.readlines()

    # Create a dictionary to store the current environment variables
    env_vars = {}
    quotes = {}
    for line in lines:
        if line.strip() and "=" in line:  # ignore empty lines and lines without '='
            key, value = line.strip().split("=", 1)
            if value.startswith('"') and value.endswith('"'):
                quotes[key] = True
                value = value[1:-1]  # Remove the quotes for processing
            else:
                quotes[key] = False
            env_vars[key] = value

    # Update the environment variables with the new values
    if api_key is not None:
        env_vars["OPENAI_API_KEY"] = api_key
    if assistant_id is not None:
        env_vars["ASSISTANT_ID"] = assistant_id
    if thread_id is not None:
        env_vars["THREAD_ID"] = thread_id
    if vector_store_id is not None:
        env_vars["VECTOR_STORE_ID"] = vector_store_id

    # Write the updated environment variables back to the .env file
    with open(path, "w") as file:
        for key, value in env_vars.items():
            if quotes.get(key, False):
                value = f'"{value}"'  # Add quotes back if they were originally present
            file.write(f"{key}={value}\n")


def create_models_dict(sync_page) -> dict:
    def convert_unix_to_human_time(unix_time):
        return datetime.utcfromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")

    model_dict = {}
    for model in sync_page.data:
        human_time = convert_unix_to_human_time(model.created)
        model_dict[model.id] = human_time
    return model_dict


def select_model(models: dict, default_model: str) -> str:
    while True:
        try:
            # Define the widths for the columns
            model_column_width = 30
            created_column_width = 19

            print(
                "\nModels available :"
                "\n------------------"
                f"\n{'No.':<4} {'Model':<{model_column_width}} {'Created':<{created_column_width}}"
                f"\n{'-'*4} {'-'*model_column_width} {'-'*created_column_width}"
            )

            # Filter the dictionary to include only 'gpt' models
            gpt_models = {k: v for k, v in models.items() if k.startswith("gpt")}

            for idx, (model, created) in enumerate(gpt_models.items()):
                print(
                    f"[{idx:02}] {model:<{model_column_width}} {created:<{created_column_width}}"
                )

            model_or_name = input(
                f"\n(a) Enter a number between 00 and {len(gpt_models) - 1:02} to select one of the above models."
                f"\n(b) Or, type the name of the model (e.g. 'gpt-5.5-turbo')."
                f"\n(c) Another option is to press 'Enter' to continue with the default model '{default_model}': \n"
                "\nUser input: "
            ).strip()

            if not model_or_name:  # User pressed 'Enter' to select the default model
                return default_model

            if model_or_name.isdigit():  # User entered a number
                model_index = int(model_or_name)
                if 0 <= model_index < len(gpt_models):
                    return list(gpt_models.keys())[model_index]
                else:
                    print(
                        f"\nError: Invalid model number. Please enter a number between 0 and {len(gpt_models) - 1:02}."
                    )

            elif model_or_name in gpt_models:  # User entered a model name
                return model_or_name
            else:
                print(
                    f'\nError: "{model_or_name}" is an invalid model name! '
                    "Please check the spelling or make a different choice."
                )

        except Exception as e:
            print(f"\nUnexpected error: {e}. Please try again.")


# # Assistants
def instructions_from_file(path: str = "instructions.txt") -> str:
    try:
        with open(path, "r") as file:
            instructions = file.read()
    except FileNotFoundError:
        print("Instructions file NOT found!")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        return instructions


def create_assistant(client, instructions, name, model):
    my_assistant = client.beta.assistants.create(
        instructions=instructions,
        name=name,
        tools=[{"type": "file_search"}],
        model=model,
    )
    return my_assistant


def retrieve_or_create_assistant(
    client, assistant_id, models, default_model, instructions
):
    while True:
        try:
            assistant = client.beta.assistants.retrieve(assistant_id)
            update_environment(assistant_id=assistant.id)
            print(f"Assistant retrieved: {assistant.name}")
            break
        except Exception:
            print("Assistant NOT found! You need to CREATE A NEW ASSISTANT.")
            assistant_name = input("Enter assistant name: ").strip()
            print(
                "\nBefore proceeding, make sure that you've written your assistant's instructions "
                'in "instructions.txt" and save this file.'
            )
            input('Press "Enter" to continue ...')

            model: str = select_model(models, default_model)
            print(model)
            assistant = create_assistant(client, instructions, assistant_name, model)
            print(f'Creating Assistant: "{assistant.name}" using {assistant.model} ...')
            break

    return assistant


def update_assistant(client, assistant_id, instructions, model):
    my_assistant = client.beta.assistants.update(
        assistant_id,
        instructions=instructions,
        model=model,
        tools=[{"type": "file_search"}],
    )
    return my_assistant


# # Threads
def create_thread(client):
    thread = client.beta.threads.create()
    return thread


def retrieve_or_create_thread(client, thread_id: str):
    while True:
        try:
            thread = client.beta.threads.retrieve(thread_id)
            print(f"Thread retrieved: {thread.id}")
            break
        except Exception:
            print("Thread NOT found!\nCreate a NEW THREAD.")
            thread = create_thread(client)
            break
    return thread


# # Vector Stores
def create_vector_store(client):
    vector_store = client.beta.vector_stores.create(name="Support FAQ")
    return vector_store


def retrieve_or_create_vector_store(client, vector_store_id):
    while True:
        try:
            vector_store = client.beta.vector_stores.retrieve(vector_store_id)
            print(f"Vector Store retrieved: {vector_store.id}")
            break
        except Exception:
            print("Vector Store NOT found!\nCreate a NEW VECTOR STORE.")
            vector_store = create_vector_store(client)
            break
    return vector_store


# # Messages
def create_message(client, content, thread_id):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content,
    )


# # Runs
def create_run(client, assistant_id, thread_id):
    run = client.beta.threads.runs.create(
        assistant_id=assistant_id, thread_id=thread_id
    )

    return run


# # Files
def upload_file(client, path, purpose="assistants"):
    try:
        with open(path, "rb") as file:
            client.files.create(file=file, purpose=purpose)
    except Exception as e:
        print(f"An error occurred: {e}")
        pass


def upload_file_batch():
    ...
    pass


def delete_files(client, files_list: list[str]) -> None:
    for file_id in files_list:
        deleted_file = client.files.delete(file_id)
        print(f"{deleted_file} deleted.")
    print("All files deleted.")
    return None


# # Vector Store Files
def create_vs_file(client, files_list, vector_store_id):
    for file_id in files_list:
        vector_store_file = client.beta.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id,
        )
        print(f"ID: {vector_store_file.id} added to {vector_store_id}.")
    return None


def delete_vs_files(client, files_list, vector_store_id):
    for file_id in files_list:
        print(f"\n \n file_id: {len(file_id)}, vector_store_id: {len(vector_store_id)}")
        print(f"\n \n file_id: {file_id}, vector_store_id: {vector_store_id}")

        deleted_file = client.beta.vector_stores.files.delete(vector_store_id, file_id)
        print(f"{deleted_file} deleted from {vector_store_id}.")
    print("All vector store files deleted.")
    return None
