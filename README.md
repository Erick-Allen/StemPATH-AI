# StemPATH-AI

StemPATH-AI is a GraphRAG STEM career research assistant built with Python, ArangoDB, O*NET data, semantic search, and optional LLM answer generation.

Users can ask career-focused questions like:

```text
What careers use Python and SQL?
What STEM jobs involve cybersecurity?
Which careers involve data analysis?
```

The system retrieves relevant O*NET career documents, expands them through graph relationships, and returns grounded career context through a Streamlit UI or CLI.

## Features

* Loads selected O*NET occupation data into ArangoDB
* Models occupations, skills, technologies, tasks, knowledge areas, and career domains as a graph
* Generates embedded RAG documents from career profiles
* Performs semantic search over occupation documents
* Expands retrieved results with graph traversal
* Supports optional LLM-generated answers through an OpenAI-compatible endpoint
* Includes both a Streamlit interface and interactive CLI

## Architecture

```text
O*NET text files
    → ingestion scripts
    → ArangoDB career graph
    → RAG documents
    → SentenceTransformer embeddings
    → semantic search
    → graph traversal
    → structured or LLM-generated answer
    → Streamlit UI / CLI
```

## Graph Model

```text
Occupation
├── requires Skill
├── uses Technology
├── performs Task
├── requires Knowledge Area
└── belongs to Career Domain

Document
└── describes Occupation
```

## Tech Stack

* Python
* ArangoDB
* Streamlit
* SentenceTransformers
* OpenAI-compatible LLM client
* Docker
* uv

## Setup

Clone the repository:

```bash
git clone https://github.com/Erick-Allen/StemPATH-AI.git
cd StemPATH-AI
```

Install dependencies:

```bash
uv sync
```

Create a `.env` file:

```bash
cp .env.example .env
```

Start ArangoDB:

```bash
docker compose up -d
```

Populate the database:

```bash
uv run python -m scripts.populate
```

This sets up the database, loads O*NET data, builds the graph, creates RAG documents, and generates embeddings.

## Run the Streamlit UI

```bash
uv run streamlit run stempath.py
```

## Run the CLI

```bash
uv run python stempath_cli.py
```

## Optional LLM Support

StemPATH-AI works without an LLM. With `USE_LLM=false`, it returns a structured answer from retrieved graph context.

To enable LLM-generated answers, run an OpenAI-compatible model and update `.env`:

```env
USE_LLM=true
LLM_URL=http://localhost:11434/v1
LLM_MODEL=qwen3
LLM_API_KEY=not-needed
```

Example local endpoints:

```text
Ollama:    http://localhost:11434/v1
LM Studio: http://localhost:1234/v1
llama.cpp: http://localhost:8080/v1
```

When enabled, the LLM receives only retrieved O*NET document context and graph context.

## Data Source

This project uses selected files from the O*NET Database by the U.S. Department of Labor, Employment and Training Administration.

O*NET database content is licensed under the Creative Commons Attribution 4.0 International License.

Files used:

```text
Occupation Data.txt
Essential Skills.txt
Software Skills.txt
Task Statements.txt
Knowledge.txt
```

## Why This Project Matters

StemPATH-AI shows how graph data and semantic retrieval can be combined to build a grounded AI research assistant.

Instead of sending a question directly to an LLM, the system first retrieves relevant occupational data, expands it through graph relationships, and then optionally uses an LLM to generate a readable answer.
