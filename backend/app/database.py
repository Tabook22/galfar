from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("report_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
    batch: Mapped[Optional["ReportBatch"]] = relationship(back_populates="reports")


class ReportBatch(Base):
    __tablename__ = "report_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    reports: Mapped[list["Report"]] = relationship(back_populates="batch")
    analyses: Mapped[list["BatchAnalysis"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["BatchChatMessage"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class BatchAnalysis(Base):
    __tablename__ = "batch_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("report_batches.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    report_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revenue: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expenses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profit_loss: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cash_flow: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assets: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    liabilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    batch: Mapped["ReportBatch"] = relationship(back_populates="analyses")


class BatchChatMessage(Base):
    __tablename__ = "batch_chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("report_batches.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    batch: Mapped["ReportBatch"] = relationship(back_populates="chat_messages")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revenue: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expenses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profit_loss: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cash_flow: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assets: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    liabilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    report: Mapped["Report"] = relationship(back_populates="analyses")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    report: Mapped["Report"] = relationship(back_populates="chat_messages")


class SavedAnalysisExport(Base):
    __tablename__ = "saved_analysis_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reports.id", ondelete="SET NULL"), nullable=True)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("report_batches.id", ondelete="SET NULL"), nullable=True)
    analysis_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True)
    batch_analysis_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("batch_analyses.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

REQUIRED_TABLES = frozenset(
    {
        "reports",
        "analyses",
        "chat_messages",
        "report_batches",
        "batch_analyses",
        "batch_chat_messages",
        "saved_analysis_exports",
    }
)


def _bind_engine() -> None:
    global engine, settings
    settings = get_settings()
    local_connect_args = (
        {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    )
    if engine is not None:
        engine.dispose()
    engine = create_engine(settings.database_url, connect_args=local_connect_args)
    SessionLocal.configure(bind=engine)


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    from app.config import _BACKEND_DIR

    current = get_settings()
    alembic_cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", current.database_url)
    command.upgrade(alembic_cfg, "head")


def _table_columns(table: str) -> set[str]:
    from sqlalchemy import inspect

    if table not in inspect(engine).get_table_names():
        return set()
    return {col["name"] for col in inspect(engine).get_columns(table)}


def _verify_schema() -> None:
    from sqlalchemy import inspect

    existing = set(inspect(engine).get_table_names())
    missing = REQUIRED_TABLES - existing
    if missing:
        Base.metadata.create_all(bind=engine)


def _repair_schema_gaps() -> None:
    """Fix partial migrations when alembic_version is ahead of the actual schema."""
    from sqlalchemy import inspect, text

    _verify_schema()

    if "reports" in inspect(engine).get_table_names() and "batch_id" not in _table_columns("reports"):
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE reports ADD COLUMN batch_id INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_batch_id ON reports (batch_id)"))

    _verify_schema()


def init_db() -> None:
    get_settings.cache_clear()
    _bind_engine()
    run_migrations()
    Base.metadata.create_all(bind=engine)
    _repair_schema_gaps()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
