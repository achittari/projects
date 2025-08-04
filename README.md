# Physiotherapy RAG Agent
## Overview
This project is a Retrieval-Augmented Generation (RAG) agent that powers a conversational interface to answer user questions about physiotherapy, massage, and therapy techniques. It leverages LlamaIndex, OpenAI's GPT models, and a curated physiotherapy dataset to provide accurate, context-aware responses.

## Features
- Conversational Q&A agent for physiotherapy-related queries.
- RAG pipeline for vector-based semantic search and answer generation.
- Custom step-back query refinement for handling vague or unsupported questions.
- Persistence of vector indexes for efficient retrieval across sessions.

## Tech Stack
- Python
- LlamaIndex (GPT Index)
- OpenAI GPT-4 / GPT-3.5-turbo
- Flask (Optional UI integration)
- CSS (For frontend styling)
- nltk (For text preprocessing)

## How It Works
- Document Indexing: Physiotherapy documents are loaded and vectorized into a persistent VectorStoreIndex.
- Query Processing: User queries are matched semantically against the index.
- Step-Back Querying: If no strong match is found, the system rephrases the query into a broader question using GPT.
- Answer Generation: Relevant documents are retrieved and GPT generates a response based on the context.
