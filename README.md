
# CodeAtlas

CodeAtlas is an AI-powered codebase intelligence tool that helps developers understand unfamiliar repositories quickly.

Simply paste a GitHub repository URL and CodeAtlas analyzes the codebase to provide:

* Natural language answers about the repository
* Architecture visualization
* Dependency relationships between files
* AI-generated summaries of the codebase

Instead of manually digging through hundreds of files, CodeAtlas gives a high-level understanding of a project in seconds.



Features

1. AI Codebase Q&A

Ask natural language questions about the repository.

Examples:

* What does this project do?
* Which files handle authentication?
* Explain the main architecture.


2. Architecture Map

Visualizes the high-level structure of the repository so you can quickly understand:

* Core modules
* Project organization
* Major components


3. Dependency Graph

Interactive graph showing relationships between files and modules.

Helps developers understand:

* File dependencies
* Module interactions
* Coupling between components


4. AI Codebase Summaries

Generate summaries at different levels:

* Entire repository overview
* Module summaries
* File-level explanations



Tech Stack

Frontend : streamlit


Backend : FastAPI, Python, Langchain, FAISS, Github API, Groq LLM.


## Installation

1. Clone the repository

  git clone https://github.com/aishik2801/CodeAtlas.git

  cd CodeAtlas


2. Backend Setup

  Inside project directory

  pip install -r requirements.txt

  uvicorn backend.api.routes:app --reload --port 8000


3. Frontend Setup

  streamlit run frontend/main.py


*Preview* 

1. Open the application
<img width="1900" height="876" alt="image" src="https://github.com/user-attachments/assets/fe7b5a6f-6077-4e17-98b2-cb7b5564841c" />

2. Paste Github repo link and click on ingest
<img width="1897" height="491" alt="Screenshot 2026-03-07 132748" src="https://github.com/user-attachments/assets/78de143b-2897-4040-ae8a-8b0c3aa5a965" />

3. Q/A mode : 
<img width="1897" height="491" alt="Screenshot 2026-03-07 132748" src="https://github.com/user-attachments/assets/7de21d28-097a-4e17-a50d-7ab813c3cc37" />

4. Repository architecture map
<img width="1897" height="491" alt="Screenshot 2026-03-07 132748" src="https://github.com/user-attachments/assets/8d448a4c-f0d8-435d-80c8-f14f5e9d9e64" />

5. Dependency Graph
<img width="1906" height="900" alt="Screenshot 2026-03-07 132434" src="https://github.com/user-attachments/assets/03654880-d35f-4c20-9cce-4a2b0a1d2f78" />

6. Mutli-Level Code summary
<img width="1903" height="888" alt="Screenshot 2026-03-07 132529" src="https://github.com/user-attachments/assets/4f5bdeab-b99f-4cdd-80f6-8b719d6fdaa4" />

<img width="1901" height="888" alt="Screenshot 2026-03-07 132547" src="https://github.com/user-attachments/assets/28336b04-71df-4454-8cce-cb7f5189bb36" />

<img width="1902" height="890" alt="Screenshot 2026-03-07 132611" src="https://github.com/user-attachments/assets/63821678-4d0d-471b-9cda-52ce5ca80d33" />






