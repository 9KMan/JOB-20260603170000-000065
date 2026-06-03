"""SQLAlchemy models for the data sync platform."""
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Text, JSON, Index, UniqueConstraint)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

Base = declarative_base()

class SourceRecord(Base):
    __tablename__ = "source_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False)
    schema_version = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    synced_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        UniqueConstraint("source_name", "external_id", name="uq_source_external_id"),
        Index("ix_source_synced_at", "synced_at"),
        Index("ix_source_name", "source_name"),
    )

class SyncLog(Base):
    __tablename__ = "sync_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(100), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False)
    records_fetched = Column(Integer, default=0)
    records_written = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    last_sync_id = Column(String(255), nullable=True)

class AuditEntry(Base):
    __tablename__ = "audit_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    level = Column(String(10), nullable=False)
    logger = Column(String(100), nullable=False)
    event = Column(String(100), nullable=False)
    source_name = Column(String(100), nullable=True)
    detail = Column(JSON, nullable=True)
    traceback = Column(Text, nullable=True)

def get_engine(database_url=None):
    url = database_url or DATABASE_URL
    return create_engine(url, pool_size=10, max_overflow=20, pool_pre_ping=True)

def create_tables(engine):
    Base.metadata.create_all(engine)