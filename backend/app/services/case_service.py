"""Case management service — CRUD, state machine, RBAC, timeline.

Implements the case lifecycle from Final Report § 4.1 / FR-CM06:
    CREATED -> ASSIGNED -> IN_PROGRESS -> HEARING_SCHEDULED -> CLOSED

Every state change, client assignment, and creation is logged to
ActivityLog so we can render an auditable timeline back to both the
lawyer and the client.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    IllegalStateTransition,
    NotAuthorized,
    NotFound,
)
from app.models.audit import ActivityLog
from app.models.case import Case, CaseParticipant
from app.models.document import Document
from app.models.enums import CaseStatus, RoleInCase, UserRole
from app.models.user import User
from app.schemas.cases import CaseCreate, CaseDetail, CaseTimelineEntry


_ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.CREATED: {CaseStatus.ASSIGNED, CaseStatus.IN_PROGRESS, CaseStatus.CLOSED},
    CaseStatus.ASSIGNED: {CaseStatus.IN_PROGRESS, CaseStatus.HEARING_SCHEDULED, CaseStatus.CLOSED},
    CaseStatus.IN_PROGRESS: {CaseStatus.HEARING_SCHEDULED, CaseStatus.CLOSED},
    CaseStatus.HEARING_SCHEDULED: {CaseStatus.IN_PROGRESS, CaseStatus.CLOSED},
    CaseStatus.CLOSED: set(),
}


def _illegal_transition(frm: CaseStatus, to: CaseStatus) -> IllegalStateTransition:
    allowed = ", ".join(s.value for s in _ALLOWED_TRANSITIONS[frm]) or "none (terminal state)"
    return IllegalStateTransition(
        message=f"Cannot transition case from {frm.value} to {to.value}.",
        hint=f"Allowed transitions from {frm.value}: {allowed}.",
    )


class CaseService:
    """All case operations live here. Routers stay thin."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ----- Read ----------------------------------------------------------

    def list_for_user(self, user: User) -> list[Case]:
        if user.role == UserRole.LAWYER:
            stmt = select(Case).where(
                or_(
                    Case.assigned_lawyer_id == user.id,
                    Case.id.in_(
                        select(CaseParticipant.case_id).where(
                            CaseParticipant.user_id == user.id
                        )
                    ),
                )
            )
        elif user.role == UserRole.CLIENT:
            stmt = select(Case).where(Case.client_id == user.id)
        else:
            return []
        return list(self.db.scalars(stmt.order_by(Case.updated_at.desc())))

    def get(self, case_id: uuid.UUID, user: User) -> Case:
        case = self.db.get(Case, case_id)
        if case is None:
            raise NotFound("Case not found.")
        self._assert_can_view(case, user)
        return case

    def detail(self, case_id: uuid.UUID, user: User) -> CaseDetail:
        case = self.get(case_id, user)
        lawyer = self.db.get(User, case.assigned_lawyer_id) if case.assigned_lawyer_id else None
        client = self.db.get(User, case.client_id) if case.client_id else None
        doc_count = (
            self.db.query(Document).filter(Document.case_id == case.id).count()
        )
        return CaseDetail(
            id=case.id,
            title=case.title,
            description=case.description,
            case_type=case.case_type,
            status=case.status,
            court_code=case.court_code,
            filing_date=case.filing_date,
            assigned_lawyer_id=case.assigned_lawyer_id,
            client_id=case.client_id,
            created_at=case.created_at,
            updated_at=case.updated_at,
            lawyer_name=lawyer.full_name if lawyer else None,
            lawyer_email=lawyer.email if lawyer else None,
            client_name=client.full_name if client else None,
            client_email=client.email if client else None,
            document_count=doc_count,
        )

    def timeline(self, case_id: uuid.UUID, user: User) -> list[CaseTimelineEntry]:
        case = self.get(case_id, user)
        entries: list[CaseTimelineEntry] = []

        # Creation event
        creator = (
            self.db.get(User, case.assigned_lawyer_id)
            if case.assigned_lawyer_id
            else None
        )
        entries.append(
            CaseTimelineEntry(
                timestamp=case.created_at,
                kind="CREATED",
                title="Case opened",
                description=f"Filed as {case.case_type.value}"
                + (f" at {case.court_code}" if case.court_code else ""),
                actor_name=creator.full_name if creator else None,
            )
        )

        # Activity log events for this case
        logs = (
            self.db.query(ActivityLog)
            .filter(
                ActivityLog.entity_type == "case",
                ActivityLog.entity_id == case.id,
            )
            .order_by(ActivityLog.created_at.asc())
            .all()
        )
        for log in logs:
            actor = self.db.get(User, log.user_id) if log.user_id else None
            if log.action == "CASE_STATUS_CHANGED":
                old = (log.old_values or {}).get("status")
                new = (log.new_values or {}).get("status")
                entries.append(
                    CaseTimelineEntry(
                        timestamp=log.created_at,
                        kind="STATUS",
                        title=f"Status: {old} → {new}",
                        actor_name=actor.full_name if actor else None,
                    )
                )
            elif log.action == "CASE_CLIENT_ASSIGNED":
                new_email = (log.new_values or {}).get("client_email")
                entries.append(
                    CaseTimelineEntry(
                        timestamp=log.created_at,
                        kind="CLIENT_ASSIGNED",
                        title="Client linked to case",
                        description=new_email,
                        actor_name=actor.full_name if actor else None,
                    )
                )
            elif log.action == "RESEARCH_SAVED_TO_CASE":
                title = (log.new_values or {}).get("title") or "Authority saved"
                entries.append(
                    CaseTimelineEntry(
                        timestamp=log.created_at,
                        kind="NOTE",
                        title=f"Research saved: {title}",
                        description=(log.new_values or {}).get("excerpt"),
                        actor_name=actor.full_name if actor else None,
                    )
                )

        # Document upload events
        documents = (
            self.db.query(Document)
            .filter(Document.case_id == case.id)
            .order_by(Document.created_at.asc())
            .all()
        )
        for doc in documents:
            uploader = self.db.get(User, doc.uploaded_by_id) if doc.uploaded_by_id else None
            entries.append(
                CaseTimelineEntry(
                    timestamp=doc.created_at,
                    kind="DOCUMENT",
                    title=f"Document uploaded: {doc.file_name}",
                    description=f"{doc.document_type.value} · {doc.file_size_bytes} bytes",
                    actor_name=uploader.full_name if uploader else None,
                )
            )

        entries.sort(key=lambda e: e.timestamp)
        return entries

    # ----- Write ---------------------------------------------------------

    def create(self, payload: CaseCreate, creator: User) -> Case:
        if creator.role != UserRole.LAWYER:
            raise NotAuthorized("Only lawyers can create cases.")

        # Resolve client by email if provided
        client: User | None = None
        if payload.client_id:
            client = self.db.get(User, payload.client_id)
            if client is None or client.role != UserRole.CLIENT:
                raise NotFound("Client not found.")
        elif payload.client_email:
            client = (
                self.db.query(User)
                .filter(User.email == payload.client_email)
                .first()
            )
            if client is None:
                raise NotFound(
                    message="No registered client with that email.",
                    hint="Ask them to sign up as a Client first, then assign the case.",
                )
            if client.role != UserRole.CLIENT:
                raise NotAuthorized(
                    message=f"User {payload.client_email} is not registered as a Client.",
                    hint="Only Client accounts can be linked to a case.",
                )

        case = Case(
            title=payload.title,
            description=payload.description,
            case_type=payload.case_type,
            court_code=payload.court_code,
            filing_date=payload.filing_date,
            assigned_lawyer_id=creator.id,
            client_id=client.id if client else None,
            status=CaseStatus.ASSIGNED if client else CaseStatus.CREATED,
        )
        self.db.add(case)
        self.db.flush()

        self.db.add(
            CaseParticipant(
                case_id=case.id, user_id=creator.id, role_in_case=RoleInCase.LAWYER
            )
        )
        if client:
            self.db.add(
                CaseParticipant(
                    case_id=case.id,
                    user_id=client.id,
                    role_in_case=RoleInCase.CLIENT,
                )
            )
            self._log(
                creator.id,
                "CASE_CLIENT_ASSIGNED",
                case.id,
                new_values={"client_email": client.email, "client_id": str(client.id)},
            )

        self.db.commit()
        self.db.refresh(case)
        return case

    def assign_client_by_email(
        self, case_id: uuid.UUID, client_email: str, user: User
    ) -> Case:
        case = self.get(case_id, user)
        if user.role != UserRole.LAWYER or case.assigned_lawyer_id != user.id:
            raise NotAuthorized("Only the assigned lawyer can assign a client.")

        client = (
            self.db.query(User).filter(User.email == client_email).first()
        )
        if client is None:
            raise NotFound(
                message="No registered client with that email.",
                hint="Ask them to sign up as a Client first.",
            )
        if client.role != UserRole.CLIENT:
            raise NotAuthorized(
                message=f"User {client_email} is not registered as a Client.",
                hint="Only Client accounts can be linked to a case.",
            )

        previous_email = None
        if case.client_id:
            prev = self.db.get(User, case.client_id)
            previous_email = prev.email if prev else None

        case.client_id = client.id
        if case.status == CaseStatus.CREATED:
            case.status = CaseStatus.ASSIGNED

        existing = (
            self.db.query(CaseParticipant)
            .filter(
                CaseParticipant.case_id == case.id,
                CaseParticipant.user_id == client.id,
                CaseParticipant.role_in_case == RoleInCase.CLIENT,
            )
            .first()
        )
        if existing is None:
            self.db.add(
                CaseParticipant(
                    case_id=case.id,
                    user_id=client.id,
                    role_in_case=RoleInCase.CLIENT,
                )
            )

        self._log(
            user.id,
            "CASE_CLIENT_ASSIGNED",
            case.id,
            old_values={"client_email": previous_email} if previous_email else None,
            new_values={"client_email": client.email, "client_id": str(client.id)},
        )
        self.db.commit()
        self.db.refresh(case)
        return case

    def update_status(
        self, case_id: uuid.UUID, new_status: CaseStatus, user: User
    ) -> Case:
        case = self.get(case_id, user)
        if user.role != UserRole.LAWYER or case.assigned_lawyer_id != user.id:
            raise NotAuthorized("Only the assigned lawyer can change case status.")

        if new_status not in _ALLOWED_TRANSITIONS[case.status]:
            raise _illegal_transition(case.status, new_status)

        previous = case.status
        case.status = new_status
        case.updated_at = datetime.now(timezone.utc)
        self._log(
            user.id,
            "CASE_STATUS_CHANGED",
            case.id,
            old_values={"status": previous.value},
            new_values={"status": new_status.value},
        )
        self.db.commit()
        self.db.refresh(case)
        return case

    def save_research_to_case(
        self,
        case_id: uuid.UUID,
        user: User,
        *,
        title: str,
        citation: str | None,
        excerpt: str | None,
        source_id: str | None,
    ) -> CaseTimelineEntry:
        """Attach a Legal Research result to a case as a timeline note."""
        case = self.get(case_id, user)
        if user.role != UserRole.LAWYER or case.assigned_lawyer_id != user.id:
            raise NotAuthorized("Only the assigned lawyer can save research to a case.")

        self._log(
            user.id,
            "RESEARCH_SAVED_TO_CASE",
            case.id,
            new_values={
                "title": title,
                "citation": citation,
                "excerpt": excerpt,
                "source_id": source_id,
            },
        )
        self.db.commit()
        return CaseTimelineEntry(
            timestamp=datetime.now(timezone.utc),
            kind="NOTE",
            title=f"Research saved: {title}",
            description=excerpt,
            actor_name=user.full_name,
        )

    # ----- Stats (used by dashboards) ------------------------------------

    def stats_for_user(self, user: User) -> dict:
        cases = self.list_for_user(user)
        active = [c for c in cases if c.status != CaseStatus.CLOSED]
        return {
            "total": len(cases),
            "active": len(active),
            "in_hearing": sum(
                1 for c in cases if c.status == CaseStatus.HEARING_SCHEDULED
            ),
            "closed": sum(1 for c in cases if c.status == CaseStatus.CLOSED),
        }

    # ----- Internal ------------------------------------------------------

    def _assert_can_view(self, case: Case, user: User) -> None:
        if user.role == UserRole.LAWYER:
            if case.assigned_lawyer_id == user.id:
                return
            participates = (
                self.db.query(CaseParticipant)
                .filter(
                    CaseParticipant.case_id == case.id,
                    CaseParticipant.user_id == user.id,
                )
                .first()
            )
            if participates:
                return
        elif user.role == UserRole.CLIENT and case.client_id == user.id:
            return
        raise NotAuthorized("You do not have access to this case.")

    def _log(
        self,
        user_id: uuid.UUID,
        action: str,
        entity_id: uuid.UUID,
        *,
        old_values: dict | None = None,
        new_values: dict | None = None,
    ) -> None:
        self.db.add(
            ActivityLog(
                user_id=user_id,
                action=action,
                entity_type="case",
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
            )
        )
