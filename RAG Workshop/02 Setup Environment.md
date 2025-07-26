autoscale: true
footer: © Zühlke APAC SWEX+DX 2024
slidenumbers: true

# [fit] **_2_**

![](bg-symbols.jpeg)

---

# RAG Workshop - Setup Environment

### We will start by setting up the environment for our RAG project.

## Estimated time: 45 minutes

### by _**Kevin Lin**_, _**Andreas Mueller**_

![](bg-rythem.jpeg)

---

# Pre-requisites

- Install Python 3.11 (3.12/13 should work but not tested)
  - Windows: [https://www.python.org/downloads/windows/]
  - MacOS: [https://www.python.org/downloads/macos/], or via [Homebrew](https://brew.sh/)
  - We'll use [virtual env](https://docs.python.org/3/library/venv.html) for easy setup and portability
- Install Pycharm IDE (Community)
  - If you only use it for the workshop, consider applying a [Free Education License](https://www.jetbrains.com/community/education/#students)

---

# Key Libraries

The following libraries will be used in our RAG implementation:

- **FastAPI**: For building APIs.
- **OpenAI**: To integrate with OpenAI's API.
- **Azure Search Documents**: For document retrieval in Azure.
- **PyPDF**: To parse PDF documents.

---

# Where do we start?

- Clone the **RAG template repo**
  - Backend API Blueprint with fastapi
  - Fully functional Angular frontend
- **Azure service integrations** in from of env. variables
  - All necessary services are ready, you just have to connect

---

# [fit] Repo Walkthrough

![](bg-terra.jpeg)

---

# Task 1: Clone repo and setup environment

**Clone** the RAG template repo

```bash
git clone https://xxx@dev.azure.com/ZuhlkeAsia/RAG%20Workshop/_git/rag-template
```

1. Checkout project **README** and follow the setup instructions
2. Run the backend and checkout the **Swagger UI**

---

# Task 2: Hello World API

Your first task is to implement a simple Helloworld API using FastAPI.

- Add a new route `/hello` that returns a JSON response with a message.
- Check your implementation by running the FastAPI server

```bash
# Use fastapi-cli to run the server in dev
fastapi dev main.py

# Alternatively, use uvicorn directly
uvicorn main:app --reload

# Or run main via PyCharm (no hot-reload)
```

---

# Task 3: Create a new **backend/.env** file for Azure integration

```bash
PYTHONPATH=./backend
# Azure OpenAI api-version. See https://aka.ms/azsdk/azure-ai-inference/azure-openai-api-versions
OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_ENDPOINT=https://oai-swex-rag-workshop-eastus.openai.azure.com/
AZURE_OPENAI_API_KEY=xxk
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
AZURE_OPENAI_CHAT_MODEL=gpt-4o-mini
CHUNK_SIZE=500
AI_SEARCH_ENDPOINT=https://srch-swex-rag-workshop.search.windows.net
AI_SEARCH_API_KEY=xxx
AI_SEARCH_INDEX_NAME=kevin-lin-rag-workshop # TODO: ADAPT THIS WITH YOUR NAME
```

# **Reminder** Everything you need to build your API are included!
 
---

# 🏆 Bonus Task: Add type definition to your API

- Use **Pydantic** to define request/response model for your API.

```python
from pydantic import BaseModel


class HelloWorldResponse(BaseModel):
    message: str


@app.get("/", response_model=HelloWorldResponse)
def read_root():
    return {"message": "Hello, World"}
```