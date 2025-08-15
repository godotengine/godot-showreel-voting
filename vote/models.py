import re
from urllib.parse import urlparse, parse_qs

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, MaxValueValidator, MinValueValidator, EmailValidator
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    email_validator = EmailValidator()

    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. The user\'s email adress'),
        validators=[email_validator],
        blank=False)
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        blank=True,
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        if self.username:
            return self.username
        else:
            return self.email

class Showreel(models.Model):
        # Constants in Model class
    OPENED_TO_SUBMISSIONS = 'OPEN'
    VOTE = 'VOTE'
    CLOSED = 'CLOSED'

    status = models.CharField(
        max_length=6,
        choices=(
            (OPENED_TO_SUBMISSIONS, 'Open to submissions'),
            (VOTE, 'Open to votes'),
            (CLOSED, 'Closed'),
        ),
        default=CLOSED,
    )

    title = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.title} ({self.status})"
    

def _validate_youtube_url(value):
    try:
        parsed = urlparse(value)
        hostname = (parsed.hostname or '').lower()
        valid_hosts = [
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "music.youtube.com",
            "youtu.be"
        ]
        if hostname not in valid_hosts:
                raise ValidationError("URL must be a valid YouTube link.")

    except Exception:
        raise ValidationError("URL must be a valid YouTube link.")

    
def _validate_steam_store_url(value):
    """
    Validates that a given URL is a Steam Store link.
    """
    try:
        parsed = urlparse(value)
        hostname = (parsed.hostname or '').lower()

        if hostname != "store.steampowered.com":
            raise ValidationError("URL must be from store.steampowered.com")

        # Optional: Check path structure for app/bundle/sub with ID
        steam_path_pattern = r"^/(app|bundle|sub)/\d+"
        if not re.match(steam_path_pattern, parsed.path):
            raise ValidationError(
                "Steam Store URL must be for an app, bundle, or subscription."
            )

    except Exception:
        raise ValidationError("Enter a valid URL.")


class Video(models.Model):
    showreel = models.ForeignKey(Showreel, blank=False, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    game = models.CharField(max_length=200, blank=False, default="")
    author_name = models.CharField(max_length=200, blank=False, default="")
    video_link = models.URLField(max_length=200, blank=False, unique=True, validators=[_validate_youtube_url])
    video_download_link = models.CharField(max_length=200, blank=False, unique=True, validators=[URLValidator()])
    contact_email = models.CharField(max_length=200, default="", blank=True, validators=[EmailValidator()])
    follow_me_link = models.CharField(max_length=200, default="", blank=True)
    steam_link = models.URLField(max_length=200, default="", blank=True, validators=[_validate_steam_store_url])

    def get_youtube_video_id(self):
        query = urlparse(self.video_link)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:8] == '/shorts/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        return None

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