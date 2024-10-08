import os
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
        print(f"{f.__name__} took {end - start} seconds.")
        return result

    return wrapper


# # Fresh Start
@timer
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
    prints.print_all_messages(client, thread_id)
    return None


# # Models
def check_env(env_path: str = ".env") -> None:
    if not os.path.exists(env_path):
        with open(env_path, "w") as file:
            file.write(
                'OPENAI_API_KEY=""\n'
                'ASSISTANT_ID=""\n'
                'THREAD_ID=""\n'
                'VECTOR_STORE_ID=""\n'
                'DEFAULT_MODEL=""\n'
            )
        print("Environment file has been created and written to.")


def update_env(
    path: str = ".env",
    api_key: str = None,
    assistant_id: str = None,
    thread_id: str = None,
    vector_store_id: str = None,
    default_model: str = None,
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
    if default_model is not None:
        env_vars["DEFAULT_MODEL"] = default_model

    # Write the updated environment variables back to the .env file
    with open(path, "w") as file:
        for key, value in env_vars.items():
            if quotes.get(key, False):
                value = f'"{value}"'  # Add quotes back if they were originally present
            file.write(f"{key}={value}\n")
    return None


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
    assistant = client.beta.assistants.create(
        instructions=instructions,
        name=name,
        tools=[{"type": "file_search"}],
        model=model,
    )
    return assistant


def retrieve_or_create_assistant(
    client, assistant_id, models, default_model, instructions
):
    while True:
        try:
            assistant = client.beta.assistants.retrieve(assistant_id)
            update_env(assistant_id=assistant.id)
            print(f'Assistant "{assistant.name}" retrieved. ID: {assistant.id}')
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


def update_assistant(client, assistant_id, vector_store_id, instructions, model):
    """
    Update the assistant's configuration with new instructions and model.

    Parameters:
        client: The API client to interact with the service.
        assistant_id (str): The ID of the assistant to update.
        vector_store_id (str): The ID of the vector store to associate.
        instructions (str): New instructions for the assistant.
        model (str): The machine learning model to use.

    Returns:
        Updated assistant object.

    Raises:
        ValueError: If parameters are invalid.
        Exception: For any API call failures.
    """
    # Validate parameters
    if not isinstance(assistant_id, str) or not isinstance(vector_store_id, str):
        raise ValueError("assistant_id and vector_store_id must be strings.")

    # Debugging: Print types of parameters
    print(f"assistant_id type: {type(assistant_id)}")
    print(f"vector_store_id type: {type(vector_store_id)}")
    print(f"instructions type: {type(instructions)}")
    print(f"model type: {type(model)}")

    try:
        my_assistant = client.beta.assistants.update(
            assistant_id,
            instructions=instructions,
            model=model,
            tools=[{"type": "file_search"}],
            tool_resources={"vector_store_ids": [vector_store_id]},  # Should be a list
        )
        return my_assistant
    except Exception as e:
        # Log the error (logging setup not shown here)
        print(f"Error updating assistant: {e}")
        raise


# # Threads
def create_thread(client):
    thread = client.beta.threads.create()
    print(f"Thread created. ID: {thread.id}")
    return thread


def retrieve_or_create_thread(client, thread_id: str):
    while True:
        try:
            thread = client.beta.threads.retrieve(thread_id)
            print(f"Thread retrieved. ID: {thread.id}")
            break
        except Exception:
            print("Thread NOT found! Creating a NEW THREAD.")
            thread = create_thread(client)
            break
    return thread


# # Vector Stores
def create_vector_store(client):
    name = input("Enter a name for the Vector Store: ").strip()
    vector_store = client.beta.vector_stores.create(name=name)
    return vector_store


def retrieve_or_create_vector_store(client, vector_store_id):
    while True:
        try:
            vector_store = client.beta.vector_stores.retrieve(vector_store_id)
            print(
                f'Vector Store "{vector_store.name}" retrieved. ID: {vector_store.id}'
            )
            break
        except Exception:
            print("Vector Store NOT found!\nCreating a NEW VECTOR STORE.")
            vector_store = create_vector_store(client)
            break
    return vector_store


def delete_vector_store_s(client, vector_stores_list: list) -> None:
    for vs in vector_stores_list:
        deleted_vector_store = client.beta.vector_stores.delete(vector_store_id=vs)
        print(f"{deleted_vector_store} deleted.")
    return None


def delete_all_vector_stores(client) -> None:
    vector_stores = client.beta.vector_stores.list()
    for vector_store in vector_stores.data:
        deleted_vector_store = client.beta.vector_stores.delete(vector_store.id)
        print(f"{deleted_vector_store} deleted.")
    print("All vector stores deleted.")
    return None


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
        thread_id=thread_id, assistant_id=assistant_id, tools=[{"type": "file_search"}]
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


def upload_file_batch(client, vector_store):
    # Ready the files for upload to OpenAI

    file_paths = []
    while True:
        file_path = input(
            "If you want to upload individual files, enter the file name including the extension: \n"
            "If you want to upload a folder, enter the folder name (e.g.: fourier books): \n"
            "If you are finished, simply press the ‘Enter’ key without pressing any other key: ",
        )
        if file_path.lower() in [""]:
            return
        else:
            try:
                file_paths.append(file_path)
            except Exception as e:
                print(f"Error: {str(e)}\n")
                continue
            else:
                file_streams = [open(path, "rb") for path in file_paths]
                file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store.id, files=file_streams
                )
        print(file_batch.file_counts)
    return file_batch


def delete_files(client, files_list: list[str]) -> None:
    """Delete all files in the list."""
    for file_id in files_list:
        deleted_file = client.files.delete(file_id)
        print(f"{deleted_file} deleted.")
    print("All files deleted.")
    return None


def manage_files(client, vector_store, choice=None) -> None:
    ...
    pass


# # Vector Store Files
def add_to_vs(client, files_list: list[str], vector_store_id: str) -> None:
    for file_id in files_list:
        vector_store_file = client.beta.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id,
        )
        print(f"ID: {vector_store_file.id} added to {vector_store_id}.")
    return None


def delete_from_vs(client, files_list, vector_store_id):
    for file_id in files_list:
        print(f"\n \n file_id: {len(file_id)}, vector_store_id: {len(vector_store_id)}")
        print(f"\n \n file_id: {file_id}, vector_store_id: {vector_store_id}")

        deleted_file = client.beta.vector_stores.files.delete(vector_store_id, file_id)
        print(f"{deleted_file} deleted from {vector_store_id}.")
    print("All vector store files deleted.")
    return None


def manage_vector_stores(client, vector_store, choice=None) -> None:
    def get_choice(prompt):
        """Helper function to get user input with error handling."""
        try:
            return input(prompt)
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    while True:
        try:
            if choice is None:
                prints.list_vs_n_files(client, vector_stores=vector_store)
                choice = get_choice(
                    "\n --> Press 'Enter' to edit (upload, add or remove) files in the current vector store, OR:\n"
                    "Choose one of the options below: \n\n"
                    + "[C]reate a new vector store\n"
                    + "[D]elete current vector store\n"
                    + "[L]ist existing vector stores\n"
                    + "[Q]uit\n\n"
                )
        except Exception as e:
            print(f"Error: {str(e)}")
            choice = get_choice(
                "\n --> NO Vector store is selected, please choose one of the options below: \n\n"
                + "[C]reate a new vector store\n"
                + "[L]ist existing vector stores\n"
                + "[Q]uit\n\n"
            )
            continue

        # Edit files in the current vector store
        if choice == "":
            manage_files(client, vector_store)
            choice = None
            break

        # Create a new vector store
        elif choice.lower() in ["c", "create"]:
            vector_store = create_vector_store(client)
            update_env(vector_store_id=vector_store.id)
            choice = None
            continue

        # Delete the current vector store
        elif choice.lower() in ["d", "delete"]:
            if vector_store:
                try:
                    delete_vector_store_s(client, [vector_store.id])
                    update_env(vector_store_id="")
                    print("Vector store deleted.")
                except Exception as e:
                    print(f"Error: {str(e)}")
                    print(
                        "No vector store found to delete. Please create a new vector store or select an existing one."
                    )
            else:
                print(
                    "No vector store is currently selected. Please create or select a vector store first."
                )
            choice = None
            continue

        # List existing vector stores
        elif choice.lower() in ["l", "list"]:
            prints.list_vs_n_files(client, vector_stores=None)
            while True:
                choice = get_choice(
                    "\n --> Choose one of the vector stores above, OR:\n\n"
                    "Press 'Enter' key to go to upper menu\n\n"
                )
                if choice == "":
                    break  # Go back to the upper menu
                elif choice.isdigit() and int(choice) in range(1, 10):
                    print("Selected vector store option not implemented yet.")
                    # Additional logic for selecting a vector store would go here
                else:
                    print("\nInvalid choice. Please try again.")
            choice = None
            continue

        # Quit the program
        elif choice.lower() in ["q", "quit"]:
            print("Exiting the program.")
            break

        # Invalid choice handling
        else:
            print("\nInvalid choice. Please try again.")
            choice = None


def chat(client, assistant_id: str, thread_id: str) -> None:
    while True:
        text = input("\nUser: ")
        if text.lower() in ["exit", "quit", "q", "bye"]:
            print("Sorry to see you go!")
            break
        else:
            pass

        create_message(client, text, thread_id)

        run = create_run(client, assistant_id, thread_id)
        while not run.completed_at:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            print(run.status)
            # time.sleep(1)

        prints.print_response(client, thread_id)

        # print_run_steps(thread_id, run.id)


# utils.print_all_messages(thread_id)
