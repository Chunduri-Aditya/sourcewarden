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
9. `planning_context.build_planning_context()` converts bounded retrieval results into the merged project's evidence contract and labels official documentation separately from community patterns.
10. The root `scripts/retrieve-rag-context.py` adapter exposes that contract to workflow planning and orchestration.
11. `PromptBuilder` combines system instructions, user task, retrieved facts, assumptions, and required output structure.
12. `WorkflowInstructionGenerator` produces the final beginner-friendly workflow recipe.

The package is designed so collection and indexing can run without API keys. OpenAI embeddings are used only when `OPENAI_API_KEY` exists and the OpenAI SDK is installed.

Live schemas from the target n8n instance remain authoritative for exact node configuration. Official documentation retrieved here is the next source of truth. Community workflow examples are candidate patterns only, and course material is untrusted background evidence.
