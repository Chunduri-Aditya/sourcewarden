from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.paths import REPO_ROOT
from web.services.dashboard_files import eval_tuning_files, manifest_summary, security_hash_status
from web.services.rag import get_planning_context
from web.services.self_improvement_status import status_for_all_runs

app = FastAPI(title="wardloom control panel")

TEMPLATES_DIR = REPO_ROOT / "web" / "templates"
STATIC_DIR = REPO_ROOT / "web" / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _render_chat(request: Request, query: str, top_k: int) -> HTMLResponse:
    result = get_planning_context(query, top_k=top_k) if query.strip() else None
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"result": result, "query": query, "top_k": top_k},
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "base.html", {})


@app.get("/chat", response_class=HTMLResponse)
def chat_get(request: Request, query: str = "", top_k: int = 5) -> HTMLResponse:
    return _render_chat(request, query, top_k)


@app.post("/chat", response_class=HTMLResponse)
def chat_post(request: Request, query: str = "", top_k: int = 5) -> HTMLResponse:
    # Scalar (non-body) parameters so this route needs no form/multipart
    # parsing dependency: query and top_k travel as URL query parameters
    # the same way for GET and POST.
    return _render_chat(request, query, top_k)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    context = {
        "runs": status_for_all_runs(),
        "files": eval_tuning_files(),
        "security": security_hash_status(),
        "manifest": manifest_summary(),
    }
    return templates.TemplateResponse(request, "dashboard.html", context)
