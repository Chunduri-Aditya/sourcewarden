# Architecture

The system is a local-first retrieval pipeline for an n8n Workflow Instruction Agent.

1. `SourceRegistry` loads and validates official n8n documentation sources.
2. `DocumentLoader` downloads source pages into `data/raw/` and writes metadata sidecars.
3. `Cleaner` removes page chrome and keeps useful documentation content.
4. `Chunker` splits cleaned docs by heading sections, then by block size when needed.
5. `EmbeddingProvider` selects OpenAI embeddings, sentence-transformer embeddings, or deterministic local hash embeddings.
6. `JsonVectorStore` persists one local collection file per RAG target under `data/indexes/`.
7. `RagRouter` selects the relevant RAG collections for a user query.
8. `RagRetriever` searches each selected collection and returns citation-ready chunks.
9. `PromptBuilder` combines system instructions, user task, retrieved facts, assumptions, and required output structure.
10. `WorkflowInstructionGenerator` produces the final beginner-friendly workflow recipe.

The package is designed so collection and indexing can run without API keys. OpenAI embeddings are used only when `OPENAI_API_KEY` exists and the OpenAI SDK is installed.

