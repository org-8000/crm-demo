"""开发用最小 API 服务：把业务 Router 挂到纯 FastAPI（SQLite + 内存知识库种子），
无需 Agno/Postgres 即可本地起后端，供前端 BFF 联调。

运行：uvicorn scripts.serve_api:app --port 8000
"""

from fastapi import FastAPI

from app.api import build_api_router
from app.db import SqlInsightRepo
from core.knowledge.kb import InMemoryKnowledgeBase
from core.tools.base import AdapterRegistry
from core.tools.web import RegulatorFetchAdapter, WebFetchAdapter
from modules.seeds import seed_payment_ontology


def create_app() -> FastAPI:
    repo = SqlInsightRepo(db_url="sqlite+pysqlite:///./mip_dev.db")
    kb = InMemoryKnowledgeBase()
    seed_payment_ontology(kb)
    reg = AdapterRegistry()
    reg.register(WebFetchAdapter())
    reg.register(RegulatorFetchAdapter())
    app = FastAPI(title="MIP dev API")
    app.include_router(build_api_router(repo=repo, knowledge=kb, registry=reg))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
