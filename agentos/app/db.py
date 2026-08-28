"""持久化层：Insight 落库（SQLAlchemy）。

设计：
- 用 JSON 列存 verdict/evidence/risk_flags/chain_context，避免 PG 专有类型(TEXT[])，
  从而 **SQLite（测试/离线）与 PostgreSQL（生产）通用**。
- 与 Agno 系统表(agno_*)同库；业务 `insight` 表由本层 create_all 或 migrations/001_init.sql 建。
- 提供 `InsightRepo` 协议 + `SqlInsightRepo`(DB) + `InMemoryInsightRepo`(测试)。

注意：本模块依赖 sqlalchemy（serve 依赖）；核心 SDK 不导入本模块。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from core.models import Insight, InsightStatus, ModuleId


class Base(DeclarativeBase):
    pass


class InsightRow(Base):
    __tablename__ = "insight"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module: Mapped[str] = mapped_column(String(8), index=True)
    subject: Mapped[str] = mapped_column(Text, default="")
    verdict: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    needs_human: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)
    linked_org_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chain_context: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def to_insight(self) -> Insight:
        created = self.created_at
        # SQLite 读回为 naive datetime；统一补 UTC 以与写入侧序列化一致
        if created is not None and created.tzinfo is None:

            created = created.replace(tzinfo=UTC)
        ins = Insight.model_validate(
            {
                "module": self.module,
                "subject": self.subject,
                "verdict": self.verdict,
                "confidence": self.confidence,
                "risk_flags": self.risk_flags or [],
                "evidence": self.evidence or [],
                "needs_human": self.needs_human,
                "status": self.status,
                "linked_org_id": self.linked_org_id,
                "chain_context": self.chain_context or {},
                "created_at": created,
            }
        )
        return ins

    def to_dict(self) -> dict:
        d = self.to_insight().model_dump(mode="json")
        d["id"] = self.id
        return d


def _row_from_insight(ins: Insight) -> InsightRow:
    return InsightRow(
        module=ins.module.value if isinstance(ins.module, ModuleId) else str(ins.module),
        subject=ins.subject,
        verdict=ins.verdict,
        confidence=ins.confidence,
        risk_flags=ins.risk_flags,
        evidence=[e.model_dump(mode="json") for e in ins.evidence],
        needs_human=ins.needs_human,
        status=ins.status.value if isinstance(ins.status, InsightStatus) else str(ins.status),
        linked_org_id=ins.linked_org_id,
        chain_context=ins.chain_context,
        created_at=ins.created_at,
    )


class InsightRepo(Protocol):
    def save(self, insight: Insight) -> dict: ...
    def list(self, module: str | None = None, status: str | None = None,
             needs_human: bool | None = None, limit: int = 100) -> list[dict]: ...
    def get(self, insight_id: int) -> dict | None: ...
    def update_status(self, insight_id: int, status: str) -> dict | None: ...


class SqlInsightRepo:
    """SQLAlchemy 实现，SQLite/PG 通用。"""

    def __init__(self, db_url: str = "sqlite+pysqlite:///:memory:", create: bool = True):
        is_sqlite = db_url.startswith("sqlite")
        is_memory = is_sqlite and ":memory:" in db_url
        connect_args = {"check_same_thread": False} if is_sqlite else {}
        engine_kwargs: dict = {"connect_args": connect_args}
        if is_memory:
            # 内存库必须单连接共享，否则各 session 看不到彼此建的表
            engine_kwargs["poolclass"] = StaticPool
        self.engine = create_engine(db_url, **engine_kwargs)
        self._Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        if create:
            Base.metadata.create_all(self.engine)

    def _session(self) -> Session:
        return self._Session()

    def save(self, insight: Insight) -> dict:
        row = _row_from_insight(insight)
        with self._session() as s:
            s.add(row)
            s.commit()
            return row.to_dict()

    def list(self, module=None, status=None, needs_human=None, limit=100) -> list[dict]:
        stmt = select(InsightRow)
        if module:
            stmt = stmt.where(InsightRow.module == module)
        if status:
            stmt = stmt.where(InsightRow.status == status)
        if needs_human is not None:
            stmt = stmt.where(InsightRow.needs_human == needs_human)
        stmt = stmt.order_by(InsightRow.created_at.desc()).limit(limit)
        with self._session() as s:
            return [r.to_dict() for r in s.scalars(stmt).all()]

    def get(self, insight_id: int) -> dict | None:
        with self._session() as s:
            row = s.get(InsightRow, insight_id)
            return row.to_dict() if row else None

    def update_status(self, insight_id: int, status: str) -> dict | None:
        with self._session() as s:
            row = s.get(InsightRow, insight_id)
            if not row:
                return None
            row.status = status
            if status != InsightStatus.NEW.value:
                row.needs_human = False
            s.commit()
            return row.to_dict()
