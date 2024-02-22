from uuid import UUID

from pydantic import BaseModel


class PostOutput(BaseModel):
    id: UUID
