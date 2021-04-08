from gdshowreelvote import settings
from django.contrib.auth.models import User

def makesuperuser(username):
    user = User.objects.get(username=username)
    user.is_staff = True
    user.is_admin = True
    user.is_superuser = True
    user.save()