from typing import Self

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.media.services.commands.sign_image_upload import UploadTicket


class UploadSignatureIn(Schema):
    model_config = ConfigDict(extra="forbid")

    # Only for the record: the browser sends the name to storage itself
    file_name: str = Field(min_length=1, max_length=255)
    # Type and size are checked by the use case, reported against these fields
    mime: str = Field(max_length=100)
    size_bytes: int = Field(ge=1)


class UploadSignatureOut(Schema):
    model_config = ConfigDict(extra="forbid")

    token: str
    expire: int
    signature: str
    public_key: str
    url_endpoint: str
    folder: str
    # ImageKit's upload address, or /dev-media/upload with the local dev adapter
    upload_url: str

    @classmethod
    def from_ticket(cls, ticket: UploadTicket) -> Self:
        return cls(
            token=ticket.token,
            expire=ticket.expire,
            signature=ticket.signature,
            public_key=ticket.public_key,
            url_endpoint=ticket.url_endpoint,
            folder=ticket.folder,
            upload_url=ticket.upload_url,
        )
