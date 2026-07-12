from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.timezone import now


class Book(models.Model):

    class Cover(models.TextChoices):
        HARD = "HARD"
        SOFT = "SOFT"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=4, choices=Cover)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(decimal_places=2, max_digits=7)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["title", "author"], name="unique_author_book"
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.author} (available: {self.inventory})"


class Borrowing(models.Model):
    borrow_date = models.DateTimeField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateTimeField(blank=True, null=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings"
    )

    @property
    def is_active(self):
        return self.actual_return_date is None

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(expected_return_date__gte=now()),
                name="expected_return_date_can_not_be_in_the_past",
            )
        ]
