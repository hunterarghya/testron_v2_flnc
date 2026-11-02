from core.errors import Invalid


class UploadRejected(Invalid):
    """The local dev adapter refused a file, as ImageKit would (bad signature, type or size)."""

    code = "upload_rejected"
    title = "The upload was refused"
