import time

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
def delete_all_messages(client, thread_id):
    print("Deleting all messages...\n")
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    if not messages.data:
        print("No messages to delete.\n")
        return
    for message in messages.data:
        client.beta.threads.messages.delete(thread_id=thread_id, message_id=message.id)
        print(f"{message.id} - {message.role} message deleted.")


def cold_start(client, thread_id):
    delete_all_messages(client, thread_id)
    time.sleep(1)
    print("Cold start!\n")
    prints.print_all_messages(thread_id)


# # Models
def select_model(models):
    while True:
        try:
            model_or_name = input(
                f"\nEnter a number between 0 and {len(models) - 1} to select one of the above models, "
                "or you can type the name of the model: "
            ).strip()
            if model_or_name.isdigit():
                model_index = int(model_or_name)
                if 0 <= model_index < len(models):
                    return models[model_index]
                else:
                    raise ValueError("Invalid model number.")
            else:
                if model_or_name in models:
                    return model_or_name
                else:
                    raise ValueError("Model name not found.")
        except ValueError as e:
            print(f"Error: {e}. Please try again.")
        except Exception:
            print("Model NOT found! Defaulting to gpt-4o-mini.")
            return "gpt-4o-mini"


# # Assistants
def create_assistant(client, instructions, name, model):
    my_assistant = client.beta.assistants.create(
        instructions=instructions,
        name=name,
        tools=[{"type": "file_search"}],
        model=model,
    )
    return my_assistant


def retrieve_or_create_assistant(client, assistant_id, models, instructions):
    while True:
        try:
            assistant = client.beta.assistants.retrieve(assistant_id)
            print("Assistant retrieved.")
            break
        except Exception:
            print("Assistant NOT found! You need to CREATE A NEW ASSISTANT.")
            assistant_name = input("Enter assistant name: ").strip()
            print("\nMake sure you've filled and saved the instructions.txt file!")
            input("Press Enter to continue ...")
            print("\nModels available:")
            print("-----------------")

            for idx, model in enumerate(models):
                print(f"{idx} : {model}")

            model = select_model(models)
            assistant = create_assistant(client, instructions, assistant_name, model)
            print("Creating assistant...")
            break
        finally:
            # Placeholder for any cleanup or final actions
            pass

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
# def create_thread(client):
#     thread = client.beta.threads.create()
#     return thread


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


def delete_files(client, files_list):
    for file_id in files_list:
        deleted_file = client.files.delete(file_id)
        print(f"{deleted_file} deleted.")
    print("All files deleted.")


# # Vector Stores
def create_vector_store(client):
    vector_store = client.beta.vector_stores.create(name="Support FAQ")
    print(vector_store.id)


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
