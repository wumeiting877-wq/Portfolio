from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.core.config import settings
from app.models.resource_account import ResourceAccount
from app.models.resource_credential import ResourceCredential, credential_audit_metadata
from app.permissions.dependencies import CurrentUser
from app.permissions.resource_scope import can_read_resource, readable_resources
from app.repositories.resource_credential_repository import ResourceCredentialRepository
from app.schemas.credential_secret import CredentialSecret, serialize_credential_secret
from app.schemas.resource_credential import ResourceCredentialCreate, ResourceCredentialUpdate
from app.security.credential_encryption import (
    CredentialConfigurationError,
    CredentialDecryptionError,
    CredentialEncryptionService,
    build_credential_aad,
)
from app.services.audit_service import write_audit


def get_credential_encryption_service() -> CredentialEncryptionService:
    if not settings.RESOURCE_CREDENTIALS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="凭据管理功能未启用",
        )
    try:
        return CredentialEncryptionService.from_base64_key(
            settings.CREDENTIAL_MASTER_KEY,
            settings.CREDENTIAL_ACTIVE_KEY_ID,
        )
    except CredentialConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="凭据管理功能不可用",
        ) from exc


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _readable_query(db: Session, current_user: CurrentUser) -> Query:
    resource_ids = readable_resources(db, current_user).with_entities(ResourceAccount.id)
    return db.query(ResourceCredential).filter(
        ResourceCredential.resource_account_id.in_(resource_ids)
    )


def list_credentials(
    db: Session,
    current_user: CurrentUser,
    *,
    resource_account_id: int | None,
    credential_type: str | None,
    status_filter: str | None,
    page: int,
    page_size: int,
) -> tuple[list[ResourceCredential], int]:
    query = _readable_query(db, current_user)
    if resource_account_id is not None:
        query = query.filter(ResourceCredential.resource_account_id == resource_account_id)
    if credential_type is not None:
        query = query.filter(ResourceCredential.credential_type == credential_type)
    if status_filter is not None:
        query = query.filter(ResourceCredential.status == status_filter)
    return ResourceCredentialRepository(db).paginate(query, page=page, page_size=page_size)


def get_readable_credential(
    db: Session, current_user: CurrentUser, credential_id: int
) -> ResourceCredential:
    credential = (
        _readable_query(db, current_user)
        .filter(ResourceCredential.id == credential_id)
        .first()
    )
    if credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="凭据不存在")
    return credential


def _check_resource_access(db: Session, current_user: CurrentUser, resource_id: int) -> None:
    if not can_read_resource(db, current_user, resource_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")


def _commit_or_conflict(db: Session, duplicate_detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=duplicate_detail) from exc
    except Exception:
        db.rollback()
        raise


def create_credential(
    db: Session,
    current_user: CurrentUser,
    payload: ResourceCredentialCreate,
    encryption: CredentialEncryptionService,
    *,
    ip_address: str | None,
) -> ResourceCredential:
    _check_resource_access(db, current_user, payload.resource_account_id)
    repo = ResourceCredentialRepository(db)
    if repo.get_by_resource_and_name(payload.resource_account_id, payload.credential_name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="同一资源下凭据名称已存在")

    try:
        credential_id = db.execute(
            text("SELECT nextval(pg_get_serial_sequence('resource_credentials', 'id'))")
        ).scalar_one()
        plaintext = serialize_credential_secret(payload.secret)
        envelope = encryption.encrypt(
            plaintext,
            build_credential_aad(credential_id, payload.resource_account_id),
        )
        credential = ResourceCredential(
            id=credential_id,
            resource_account_id=payload.resource_account_id,
            credential_name=payload.credential_name,
            credential_type=payload.secret.credential_type,
            encrypted_payload=envelope.ciphertext,
            encryption_nonce=envelope.nonce,
            encryption_version=envelope.encryption_version,
            key_id=envelope.key_id,
            status="ACTIVE",
            expires_at=payload.expires_at,
            last_rotated_at=_now(),
            rotation_interval_days=payload.rotation_interval_days,
            created_by_user_id=current_user.id,
            updated_by_user_id=current_user.id,
        )
        db.add(credential)
        write_audit(
            db,
            operator_user_id=current_user.id,
            action="RESOURCE_CREDENTIAL_CREATE",
            module="resource_credentials",
            target_type="resource_credential",
            target_id=credential.id,
            after_data=credential_audit_metadata(credential),
            ip_address=ip_address,
        )
        _commit_or_conflict(db, "同一资源下凭据名称已存在")
        db.refresh(credential)
        return credential
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def update_credential(
    db: Session,
    current_user: CurrentUser,
    credential_id: int,
    payload: ResourceCredentialUpdate,
    *,
    ip_address: str | None,
) -> ResourceCredential:
    credential = get_readable_credential(db, current_user, credential_id)
    before = credential_audit_metadata(credential)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(credential, field, value)
    credential.updated_by_user_id = current_user.id
    write_audit(
        db,
        operator_user_id=current_user.id,
        action="RESOURCE_CREDENTIAL_UPDATE",
        module="resource_credentials",
        target_type="resource_credential",
        target_id=credential.id,
        before_data=before,
        after_data=credential_audit_metadata(credential),
        ip_address=ip_address,
    )
    _commit_or_conflict(db, "同一资源下凭据名称已存在")
    db.refresh(credential)
    return credential


def _verify_existing_ciphertext(
    credential: ResourceCredential, encryption: CredentialEncryptionService
) -> None:
    if credential.key_id != encryption.key_id:
        raise CredentialDecryptionError("Credential decryption failed")
    encryption.decrypt(
        credential.encrypted_payload,
        credential.encryption_nonce,
        build_credential_aad(
            credential.id,
            credential.resource_account_id,
            credential.encryption_version,
        ),
    )


def rotate_credential(
    db: Session,
    current_user: CurrentUser,
    credential_id: int,
    secret: CredentialSecret,
    encryption: CredentialEncryptionService,
    *,
    ip_address: str | None,
) -> ResourceCredential:
    credential = get_readable_credential(db, current_user, credential_id)
    if secret.credential_type != credential.credential_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="轮换凭据类型必须与原凭据一致",
        )
    try:
        _verify_existing_ciphertext(credential, encryption)
        envelope = encryption.encrypt(
            serialize_credential_secret(secret),
            build_credential_aad(credential.id, credential.resource_account_id),
        )
    except CredentialDecryptionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="凭据完整性校验失败",
        ) from exc

    before = credential_audit_metadata(credential)
    credential.encrypted_payload = envelope.ciphertext
    credential.encryption_nonce = envelope.nonce
    credential.encryption_version = envelope.encryption_version
    credential.key_id = envelope.key_id
    credential.last_rotated_at = _now()
    credential.updated_by_user_id = current_user.id
    write_audit(
        db,
        operator_user_id=current_user.id,
        action="RESOURCE_CREDENTIAL_ROTATE",
        module="resource_credentials",
        target_type="resource_credential",
        target_id=credential.id,
        before_data=before,
        after_data=credential_audit_metadata(credential),
        ip_address=ip_address,
    )
    _commit_or_conflict(db, "凭据轮换失败")
    db.refresh(credential)
    return credential


def set_credential_status(
    db: Session,
    current_user: CurrentUser,
    credential_id: int,
    new_status: str,
    *,
    ip_address: str | None,
) -> ResourceCredential:
    credential = get_readable_credential(db, current_user, credential_id)
    before = credential_audit_metadata(credential)
    credential.status = new_status
    credential.updated_by_user_id = current_user.id
    write_audit(
        db,
        operator_user_id=current_user.id,
        action="RESOURCE_CREDENTIAL_STATUS_UPDATE",
        module="resource_credentials",
        target_type="resource_credential",
        target_id=credential.id,
        before_data=before,
        after_data=credential_audit_metadata(credential),
        ip_address=ip_address,
    )
    _commit_or_conflict(db, "凭据状态修改失败")
    db.refresh(credential)
    return credential
