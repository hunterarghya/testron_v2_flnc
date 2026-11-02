"""Run use cases at the same moment, each on its own database connection (testing_strategy.md,
concurrency tests). Tests using it need `pytest.mark.django_db(transaction=True)`."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import connection

Outcome = object | BaseException


def run_together(*work: Callable[[], object]) -> list[Outcome]:
    """Start every callable at once; each one's result, or the exception it raised."""
    start = Barrier(len(work))

    def run(task: Callable[[], object]) -> Outcome:
        start.wait()
        try:
            return task()
        except BaseException as error:  # the test inspects every outcome
            return error
        finally:
            # Each thread opened its own connection; leaving it open blocks the test database
            connection.close()

    with ThreadPoolExecutor(max_workers=len(work)) as pool:
        return list(pool.map(run, work))
