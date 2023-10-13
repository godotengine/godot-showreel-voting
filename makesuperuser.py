from gdshowreelvote import settings
from vote.models import User

def makesuperuser(email):
    user = User.objects.get(email=email)
    user.is_staff = True
    user.is_superuser = True
    user.save()