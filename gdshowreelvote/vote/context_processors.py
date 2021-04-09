from django.conf import settings

from .models import Showreel


def common(request):
    has_open_showreels = Showreel.objects.filter(status=Showreel.OPENED_TO_SUBMISSIONS).exists()
    has_voting_showreels = Showreel.objects.filter(status=Showreel.VOTE).exists()
    can_vote = (not settings.VOTE_ONLY_STAFF_CAN_VOTE) or request.user.is_staff
    return {
        'has_open_showreels': has_open_showreels,
        'has_voted_showreels' : has_voting_showreels,
        'can_vote': can_vote,
    }