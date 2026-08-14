FROM python:3.11-slim

WORKDIR /app

COPY web/requirements.txt web/requirements.txt
RUN pip install --no-cache-dir -r web/requirements.txt

COPY . .

# n8n_rag_system/data/ is gitignored (see .gitignore) and n8n_rag_system/data/raw/
# is also excluded from the build context by .dockerignore. A freshly built image
# therefore has no RAG index until n8n_rag_system/data/indexes/ is volume-mounted
# at deploy time or rebuilt post-deploy (python3 n8n_rag_system/scripts/*.py from
# n8n_rag_system/). Until then, GET/POST /chat correctly degrades to a
# "no_retrieved_evidence" result -- that is expected behavior, not a bug.

EXPOSE 8000

CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]
