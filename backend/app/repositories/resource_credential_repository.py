from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.models.resource_credential import ResourceCredential


class ResourceCredentialRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, credential_id: int) -> ResourceCredential | None:
        return self.db.get(ResourceCredential, credential_id)

    def get_by_resource_and_name(
        self, resource_account_id: int, credential_name: str
    ) -> ResourceCredential | None:
        return (
            self.db.query(ResourceCredential)
            .filter(
                ResourceCredential.resource_account_id == resource_account_id,
                ResourceCredential.credential_name == credential_name,
            )
            .first()
        )

    def paginate(
        self, query: Query, *, page: int, page_size: int
    ) -> tuple[list[ResourceCredential], int]:
        total = query.order_by(None).with_entities(func.count(ResourceCredential.id)).scalar()
        items = (
            query.order_by(ResourceCredential.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, int(total or 0)
