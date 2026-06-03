"""Incremental sync engine with upsert deduplication."""
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from src.models import SourceRecord, SyncLog, get_engine
from src.api_client import create_client
from src.schema_registry import registry

logger = logging.getLogger(__name__)

class SyncEngine:
    def __init__(self, source_name: str, api_base_url: str, api_key: str, database_url: str):
        self.source_name = source_name
        self.client = create_client(api_base_url, api_key)
        self.engine = get_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)()

    def run_sync(self) -> SyncLog:
        sync_log = SyncLog(
            source_name=self.source_name,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.Session.add(sync_log)
        self.Session.commit()
        session = self.Session

        try:
            last_sync_id = self._get_last_sync_id(session)
            records_fetched = 0
            records_written = 0
            records_updated = 0

            for page in self.client.paginate(f"/{self.source_name}", params={} if not last_sync_id else {"after": last_sync_id}):
                records_fetched += len(page)
                for raw_record in page:
                    errors = registry.validate(self.source_name, raw_record)
                    if errors:
                        logger.warning(f"Validation errors for record {raw_record.get('id', '?')}: {errors}")
                        continue
                    normalized = registry.transform(self.source_name, raw_record)
                    written, updated = self._upsert_record(session, normalized)
                    records_written += written
                    records_updated += updated
                    last_sync_id = normalized.get("id")
                if records_fetched >= 10000:
                    logger.info(f"Batch limit reached ({records_fetched} records)")
                    break

            sync_log.records_fetched = records_fetched
            sync_log.records_written = records_written
            sync_log.records_updated = records_updated
            sync_log.status = "success"
            sync_log.completed_at = datetime.now(timezone.utc)
            sync_log.last_sync_id = last_sync_id
            session.commit()
            logger.info(f"Sync complete: fetched={records_fetched} written={records_written} updated={records_updated}")
            return sync_log

        except Exception as e:
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.now(timezone.utc)
            session.commit()
            logger.error(f"Sync failed: {e}")
            raise

    def _get_last_sync_id(self, session) -> Optional[str]:
        log = session.query(SyncLog).filter(
            SyncLog.source_name == self.source_name,
            SyncLog.status == "success"
        ).order_by(SyncLog.completed_at.desc()).first()
        return log.last_sync_id if log else None

    def _upsert_record(self, session, record: dict) -> tuple:
        external_id = record.get("id")
        if not external_id:
            return 0, 0
        stmt = pg_insert(SourceRecord).values(
            source_name=self.source_name,
            external_id=str(external_id),
            schema_version=record.get("_schema_version", "1.0"),
            payload=record.get("_raw", record),
            last_updated=record.get("updated_at"),
            synced_at=datetime.now(timezone.utc),
        ).on_conflict_do_update(
            index_elements=["source_name", "external_id"],
            set_={
                "schema_version": record.get("_schema_version", "1.0"),
                "payload": record.get("_raw", record),
                "last_updated": record.get("updated_at"),
                "synced_at": datetime.now(timezone.utc),
            }
        )
        result = session.execute(stmt)
        return 1, 1 if result.rowcount > 0 else 0