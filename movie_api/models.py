from django.db import models
from django.contrib.auth.models import User


class Watchlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watchlist"
    )
    movie_id = models.IntegerField()
    title = models.CharField(max_length=255)
    poster_path = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    release_date = models.CharField(
        max_length=30,
        blank=True
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "movie_id"],
                name="unique_user_watchlist_movie"
            )
        ]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"


# Create your models here.
