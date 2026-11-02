from django.db import models

from modules.students.models.student import Student


class PerformanceShare(models.Model):
    """The row exists exactly while a student may see their own performance (domain_model §3.2)."""

    student = models.OneToOneField(
        Student, primary_key=True, on_delete=models.CASCADE, related_name="+"
    )
    shared_since = models.DateTimeField()

    class Meta:
        db_table = "performance_shares"

    def __str__(self) -> str:
        return str(self.student_id)
