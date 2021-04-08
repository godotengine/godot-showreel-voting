from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator, MaxValueValidator, MinValueValidator

class Showreel(models.Model):
        # Constants in Model class
    OPENED_TO_SUBMISSIONS = 'OPEN'
    VOTE = 'VOTE'
    CLOSED = 'CLOSED'

    status = models.CharField(
        max_length=6,
        choices=(
            (OPENED_TO_SUBMISSIONS, 'Open to submissions'),
            (VOTE, 'Vote'),
            (CLOSED, 'Closed'),
        ),
        default=CLOSED,
    )

    title = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.title} ({self.status})"

class Video(models.Model):
    showreel = models.ForeignKey(Showreel, blank=False, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    game = models.CharField(max_length=200, blank=False, default="")
    author_name = models.CharField(max_length=200, blank=False, default="")
    video_link = models.CharField(max_length=200, blank=False, unique=True, validators=[URLValidator()])
    follow_me_link = models.CharField(max_length=200, default="", blank=True, validators=[URLValidator()])

    def __str__(self):
        return f"{self.author} - {self.game} - {self.video_link}"

class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    rating = models.IntegerField(
        default=0,
        validators=[
            MaxValueValidator(5),
            MinValueValidator(1)
        ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}\'s vote on {self.video.video_link}. ({self.rating}/5)" 