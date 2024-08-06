# README

## Overview

This repository contains a Python script that interacts with OpenAI's API to create and manage an AI assistant. The assistant is designed to respond in a specific style and help with questions related to a provided document. The script includes functionalities for managing files, vector stores, and threads to facilitate interactions with the AI assistant.

## Prerequisites

- Python 3.7 or higher
- `dotenv` library for environment variable management
- `openai` library for interacting with OpenAI's API
- Custom `prints` and `utils` modules for additional functionalities (ensure these are included in your repository)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/burakai/dedibot.git
    cd dedibot
    ```

2. Install required packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the root directory of your project and add your OpenAI API key:
    ```
    OPENAI_API_KEY="your-openai-api-key"
    ```

## Usage

1. **Initialize the Assistant**:
    - The script starts by loading environment variables and setting up the OpenAI client.
    - It configures the assistant with predefined instructions and attempts to retrieve an existing assistant using `assistant_id`. If not found, it prompts to create a new assistant.

2. **Manage Threads**:
    - The script tries to retrieve an existing thread using `thread_id`. If not found, it prompts to create a new thread.

3. **Manage Vector Stores**:
    - The script attempts to retrieve an existing vector store using `vector_store_id`. If not found, the script exits.

4. **File Handling**:
    - The script lists existing files and provides options to upload new files, continue with existing files, or start with no files.
    - Uploaded files are listed and used to create a vector store file.

5. **Interaction**:
    - The script provides a continuous prompt for user input to interact with the assistant.
    - User inputs are sent to the assistant, and responses are retrieved and displayed.

## Running the Script

To run the script, execute the following command in your terminal:

```sh
python script.py
