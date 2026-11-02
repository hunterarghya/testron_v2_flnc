"""The one NinjaAPI: mounts every module's router under /api/v1 and the error handlers."""

from django.conf import settings
from ninja import NinjaAPI, Router
from ninja.operation import Operation

from core.http.problems import register_problem_handlers
from modules.assignments.routes import router as assignments
from modules.authoring.routes import router as authoring
from modules.delivery.routes import router as delivery
from modules.grading.routes import router as grading
from modules.identity.routes import router as identity
from modules.media.routes import router as media
from modules.results.routes import router as results
from modules.students.routes import router as students
from modules.tagging.routes import router as tagging

# Each path belongs to exactly one module; the routers carry full paths (project_structure §6)
ROUTERS: tuple[Router, ...] = (
    identity,
    students,
    tagging,
    media,
    authoring,
    assignments,
    delivery,
    grading,
    results,
)


class Api(NinjaAPI):
    def get_openapi_operation_id(self, operation: Operation) -> str:
        # Controllers are named after their use case, which is unique across the API
        return operation.view_func.__name__


api = Api(
    title="Test Platform API",
    version="1",
    urls_namespace="api",
    # The interactive docs and the raw schema are for development only
    docs_url="/docs" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)
register_problem_handlers(api)
for router in ROUTERS:
    api.add_router("", router)
