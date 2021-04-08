from .models import Showreel

def common(request):
    has_open_showreels = Showreel.objects.filter(status=Showreel.OPENED_TO_SUBMISSIONS).exists()
    has_voting_showreels = Showreel.objects.filter(status=Showreel.VOTE).exists()
    return {
        'has_open_showreels': has_open_showreels,
        'has_voted_showreels' : has_voting_showreels,
    }