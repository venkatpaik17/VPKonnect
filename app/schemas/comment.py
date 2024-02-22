from uuid import UUID

from pydantic import BaseModel


class CommentOutput(BaseModel):
    id: UUID
