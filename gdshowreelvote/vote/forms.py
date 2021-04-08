from django.conf import settings

from django.forms import ModelForm
from django import forms

from .models import Video, Showreel

from django.core.exceptions import ValidationError

class SubmissionForm(ModelForm):
    showreel = forms.ModelChoiceField(queryset=Showreel.objects.filter(status=Showreel.OPENED_TO_SUBMISSIONS), empty_label=None)

    class Meta:
        model = Video
        fields = '__all__'
        exclude = ["author"]
        labels = {
            'game': 'Game title',
            'follow_me_link' : 'Where to follow me',
            'author_name' : 'Author or studio'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        return super(SubmissionForm, self).__init__(*args, **kwargs)


    def save(self, *args, **kwargs):
        submission = super(SubmissionForm, self).save(commit=False, *args, **kwargs)
        submission.author = self.user
        submission.save()
        return submission

    def clean(self):
        cleaned_data = super().clean()
        showreel = cleaned_data.get("showreel")

        if len(Video.objects.filter(showreel=showreel, author=self.user)) >= settings.VOTE_MAX_SUBMISSIONS_PER_SHOWREEL:
            self.add_error('showreel', ValidationError(f"You already have {settings.VOTE_MAX_SUBMISSIONS_PER_SHOWREEL} submissions on this showreel, no more submissions are allowed. Please avoid submitting the same game several times."))