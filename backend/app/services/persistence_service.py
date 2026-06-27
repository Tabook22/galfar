"""Restore and reconcile on-disk data with the database on startup."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import Settings
from app.database import Analysis, Report, SavedAnalysisExport
from app.services.report_parser import ReportParser
from app.services.storage_manifest import StorageManifest, build_manifest_entry


class PersistenceService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.parser = ReportParser()
        self.manifest = StorageManifest(settings.storage_path / "galfar_manifest.json")

    def sync_all(self, db: Session) -> None:
        self._consolidate_upload_dirs()
        self._reconcile_upload_paths(db)
        self._sync_reports_from_manifest(db)
        self._sync_saved_analyses_from_disk(db)
        self._sync_reports_from_saved_exports(db)
        db.commit()

    def record_report(self, report: Report) -> None:
        self.manifest.upsert_report(
            build_manifest_entry(
                report_id=report.id,
                filename=report.filename,
                original_filename=report.original_filename,
                file_path=report.file_path,
                file_type=report.file_type,
                file_size=report.file_size,
                status=report.status,
                created_at=report.created_at,
            )
        )

    def remove_report(self, file_path: str) -> None:
        self.manifest.remove_report(file_path)

    def _legacy_upload_dirs(self) -> list[Path]:
        canonical = self.settings.upload_path.resolve()
        candidates = [
            self.settings.storage_path / "uploads",
            self.settings.storage_path.parent / "uploads",
        ]
        return [path.resolve() for path in candidates if path.resolve() != canonical]

    def _consolidate_upload_dirs(self) -> None:
        canonical = self.settings.upload_path.resolve()
        canonical.mkdir(parents=True, exist_ok=True)

        for source in self._legacy_upload_dirs():
            source = source.resolve()
            if not source.exists() or source == canonical:
                continue
            for item in source.iterdir():
                if not item.is_file():
                    continue
                target = canonical / item.name
                if target.exists():
                    item.unlink(missing_ok=True)
                else:
                    shutil.move(str(item), str(target))

            if source.exists() and not any(source.iterdir()):
                source.rmdir()

    def _reconcile_upload_paths(self, db: Session) -> None:
        canonical = self.settings.upload_path.resolve()
        path_map: dict[str, str] = {}

        for report in db.query(Report).all():
            current = Path(report.file_path)
            target = canonical / report.filename
            if current.resolve() == target:
                continue
            if not target.exists() and current.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(current), str(target))
            if target.exists():
                old_path = report.file_path
                report.file_path = str(target)
                path_map[old_path] = report.file_path

        if path_map:
            entries = self.manifest.list_reports()
            for entry in entries:
                old_path = entry.get("file_path")
                if old_path in path_map:
                    entry["file_path"] = path_map[old_path]
                elif old_path:
                    entry["file_path"] = str(canonical / entry.get("filename", Path(old_path).name))
            self.manifest._save(entries)

        self._reconcile_saved_export_paths(path_map, canonical)

    def _reconcile_saved_export_paths(self, path_map: dict[str, str], canonical: Path) -> None:
        saved_dir = self.settings.saved_analyses_path
        if not saved_dir.exists():
            return

        for json_file in saved_dir.glob("*.json"):
            try:
                content = json.loads(json_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            report_meta = content.get("report")
            if not isinstance(report_meta, dict):
                continue

            old_path = report_meta.get("file_path")
            if not old_path:
                continue

            new_path = path_map.get(old_path)
            if not new_path and "storage/uploads" in old_path.replace("\\", "/"):
                new_path = str(canonical / report_meta.get("filename", Path(old_path).name))
            if new_path and new_path != old_path:
                report_meta["file_path"] = new_path
                json_file.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")

    def _sync_reports_from_manifest(self, db: Session) -> None:
        known_paths = {row.file_path for row in db.query(Report.file_path).all()}

        for entry in self.manifest.list_reports():
            file_path = entry.get("file_path")
            if not file_path or file_path in known_paths:
                continue
            path = Path(file_path)
            if not path.exists():
                canonical = self.settings.upload_path / path.name
                if canonical.exists():
                    file_path = str(canonical)
                    path = canonical
                else:
                    continue

            report = Report(
                filename=entry.get("filename") or path.name,
                original_filename=entry.get("original_filename") or path.name,
                file_path=file_path,
                file_type=entry.get("file_type") or path.suffix.lstrip("."),
                file_size=entry.get("file_size") or path.stat().st_size,
                status=entry.get("status") or "uploaded",
            )
            if created := entry.get("created_at"):
                try:
                    report.created_at = datetime.fromisoformat(created)
                    report.updated_at = report.created_at
                except ValueError:
                    pass

            db.add(report)
            db.flush()
            known_paths.add(file_path)
            self._ensure_extracted_text(report, db)

    def _sync_saved_analyses_from_disk(self, db: Session) -> None:
        saved_dir = self.settings.saved_analyses_path
        if not saved_dir.exists():
            return

        known_files = {row.file_path for row in db.query(SavedAnalysisExport.file_path).all()}

        for json_file in sorted(saved_dir.glob("*.json")):
            file_path = str(json_file.resolve())
            if file_path in known_files:
                continue
            try:
                content = json.loads(json_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            title = str(content.get("title") or json_file.stem).strip()
            if not title:
                continue

            source_type = content.get("source_type") or "report"
            source_name = content.get("source_name") or title
            record = SavedAnalysisExport(
                title=title,
                filename=json_file.name,
                file_path=file_path,
                source_type=source_type,
                source_name=source_name,
                report_id=content.get("report_id"),
                batch_id=content.get("batch_id"),
                analysis_id=content.get("analysis_id"),
                batch_analysis_id=content.get("batch_analysis_id"),
            )
            saved_at = content.get("saved_at")
            if saved_at:
                try:
                    record.created_at = datetime.fromisoformat(saved_at)
                except ValueError:
                    pass
            db.add(record)
            known_files.add(file_path)

    def _sync_reports_from_saved_exports(self, db: Session) -> None:
        saved_dir = self.settings.saved_analyses_path
        if not saved_dir.exists():
            return

        for json_file in saved_dir.glob("*.json"):
            try:
                content = json.loads(json_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            report_meta = content.get("report")
            if not isinstance(report_meta, dict):
                continue

            file_path = report_meta.get("file_path")
            if not file_path:
                continue

            path = Path(file_path)
            if not path.exists():
                fallback = self.settings.upload_path / (report_meta.get("filename") or path.name)
                if fallback.exists():
                    file_path = str(fallback)
                    path = fallback
                else:
                    continue

            existing = db.query(Report).filter(Report.file_path == file_path).first()
            if existing:
                self._restore_analysis_if_missing(db, existing, content)
                continue

            report = Report(
                filename=report_meta.get("filename") or path.name,
                original_filename=report_meta.get("original_filename") or path.name,
                file_path=file_path,
                file_type=report_meta.get("file_type") or path.suffix.lstrip("."),
                file_size=report_meta.get("file_size") or path.stat().st_size,
                status="analyzed",
            )
            db.add(report)
            db.flush()
            self._ensure_extracted_text(report, db)
            self._restore_analysis_if_missing(db, report, content)
            self.record_report(report)

    def _restore_analysis_if_missing(self, db: Session, report: Report, content: dict) -> None:
        analysis_data = content.get("analysis")
        if not isinstance(analysis_data, dict):
            return

        has_completed = (
            db.query(Analysis)
            .filter(Analysis.report_id == report.id, Analysis.status == "completed")
            .first()
        )
        if has_completed:
            return

        analysis = Analysis(
            report_id=report.id,
            status="completed",
            summary=analysis_data.get("summary"),
            revenue=analysis_data.get("revenue"),
            expenses=analysis_data.get("expenses"),
            profit_loss=analysis_data.get("profit_loss"),
            cash_flow=analysis_data.get("cash_flow"),
            assets=analysis_data.get("assets"),
            liabilities=analysis_data.get("liabilities"),
            risks=analysis_data.get("risks"),
            strengths=analysis_data.get("strengths"),
            weaknesses=analysis_data.get("weaknesses"),
            recommendations=analysis_data.get("recommendations"),
        )
        created_at = analysis_data.get("created_at")
        if created_at:
            try:
                analysis.created_at = datetime.fromisoformat(created_at)
            except ValueError:
                pass
        db.add(analysis)
        report.status = "analyzed"

    def _ensure_extracted_text(self, report: Report, db: Session) -> None:
        if report.extracted_text:
            return
        try:
            report.extracted_text = self.parser.extract_text(report.file_path, report.file_type)
        except Exception:
            return
