from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.generic.list import ListView
from django.views.generic import CreateView, DeleteView, UpdateView, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ModelFormMixin, ProcessFormView
from django.views.generic.base import TemplateView
from django.views import View
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

from .models import Video, Vote, Showreel, User
from .forms import *

import csv

# Display a random video to be rated
class VoteView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Vote
    fields = ["rating"]
    success_url = reverse_lazy('vote')
    template_name = "vote/vote.html"

    def _get_not_rated_video(self):
        # Get list of already voted videos
        voted = Vote.objects.filter(user=self.request.user).values_list('video__id', flat=True)

        # Get a not rated video
        not_rated_videos = Video.objects.filter(showreel__status="VOTE").exclude(author=self.request.user).exclude(id__in=voted)

        if len(not_rated_videos) == 0:
            return None
        else:
            hash = (self.request.user.email, len(not_rated_videos)).__hash__()
            video = not_rated_videos[hash % len(not_rated_videos)]
            return video

    def _get_amount_to_rate(self):
        # Get amount of videos that can be rated
        return len(Video.objects.filter(showreel__status="VOTE").exclude(author=self.request.user))

    def _get_amount_already_rated(self):
        # Get amount of videos already rated
        return len(Vote.objects.filter(user=self.request.user).values_list('video__id', flat=True))

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.video = self._get_not_rated_video()
        obj.save()
        return super(VoteView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["video"] = self._get_not_rated_video()
        context["amount_total"] = self._get_amount_to_rate()
        context["amount_rated"] = self._get_amount_already_rated()
        context["can_undo"] = Vote.objects.filter(user=self.request.user, video__showreel__status=Showreel.VOTE).exists()
        return context

    def test_func(self):
        return (not settings.VOTE_ONLY_STAFF_CAN_VOTE) or self.request.user.is_staff

    def handle_no_permission(self):
        return redirect('submissions')

# Delete the last vote done
class LastVoteDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    http_method_names = ['post', 'delete']
    success_url = reverse_lazy('vote')

    def get_object(self, queryset=None):
        # Get last vote to delete it
        return Vote.objects.filter(user=self.request.user, video__showreel__status=Showreel.VOTE).order_by('created_at').last()

    def test_func(self):
        if (not settings.VOTE_ONLY_STAFF_CAN_VOTE) or self.request.user.is_staff:
            return Vote.objects.filter(user=self.request.user, video__showreel__status=Showreel.VOTE).exists()
        else:
            return False

    def handle_no_permission(self):
        return redirect('submissions')

# Either create or update a vote for a given video. Only POST.
class VoteVideoView(LoginRequiredMixin, UserPassesTestMixin, ModelFormMixin, ProcessFormView):
    http_method_names = ['post']
    model = Vote
    fields = ["rating"]

    def get_object(self, *args, **kwargs):
        video = Video.objects.get(pk=self.kwargs["video_pk"])
        try:
            return Vote.objects.get(video=video, user=self.request.user)
        except Vote.DoesNotExist:
            return None

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.video = Video.objects.get(pk=self.kwargs["video_pk"])
        obj.save()
        return super(VoteVideoView, self).form_valid(form)

    def form_invalid(self, form):
        return JsonResponse(status=400, data=form.errors)

    def get_success_url(self): # Should be useless.
        video = Video.objects.get(pk=self.kwargs["video_pk"])
        return reverse('showreel-overview', args=[video.showreel.id])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(VoteVideoView, self).post(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_staff

# Display the list of a user's submissions
class UserVideoListView(LoginRequiredMixin, ListView):
    model = Video
    template_name = "vote/video_user_list.html"

    def get_queryset(self):
        return Video.objects.filter(author=self.request.user).exclude(showreel__status=Showreel.CLOSED)

# Create a new submission
class VideoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Video
    form_class = SubmissionForm
    success_url = reverse_lazy('submissions')

    def get_form_kwargs(self):
        kwargs = super(VideoCreateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def test_func(self):
        return Showreel.objects.filter(status=Showreel.OPENED_TO_SUBMISSIONS).exists()

# Update a submission
class VideoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Video
    form_class = SubmissionForm
    success_url = reverse_lazy('submissions')

    def get_form_kwargs(self):
        kwargs = super(VideoUpdateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def test_func(self):
        obj = self.get_object()
        return (self.request.user == obj.author) and obj.showreel.status == Showreel.OPENED_TO_SUBMISSIONS

# Delete a submission
class VideoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Video
    success_url = reverse_lazy('submissions')

    def test_func(self):
        obj = self.get_object()
        return (self.request.user == obj.author) and obj.showreel.status == Showreel.OPENED_TO_SUBMISSIONS

# Display the list of all open submissions
class ShowreelView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Showreel

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["video_list"] = []
        for video in Video.objects.filter(showreel=self.object):
            video_and_vote = {}
            video_and_vote["video"] = video
            video_and_vote["vote"] = Vote.objects.filter(video=video, user=self.request.user).first()
            context["video_list"].append(video_and_vote)
        return context

    def test_func(self):
        return self.request.user.is_staff

class ShowreelListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Showreel
    ordering = ['status', 'title']

    def test_func(self):
        return self.request.user.is_staff

# Display the about page
class AboutView(TemplateView):
    template_name = "vote/about.html"

# Download a csv of a showreel results
class ShowreelResultsAsCSVView(LoginRequiredMixin, UserPassesTestMixin, SingleObjectMixin, View):
    model=Showreel

    def get(self, request, *args, **kwargs):
        # Create the HttpResponse object with the appropriate CSV header.

        showreel = self.get_object()

        votes = Vote.objects.filter(video__showreel=showreel).select_related('video', 'user')
        video_set = Video.objects.filter(showreel=showreel)
        user_set = votes.values_list('user', flat=True).distinct()
        user_set = User.objects.filter(id__in=user_set)

        # Store the rating per user and video
        d = {}
        for vote in votes:
             d[(vote.user.id, vote.video.id)] = vote.rating

        # Build the CSV respose
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="results-showreel{showreel.id}.csv"'

        writer = csv.writer(response)
        writer.writerow(["Author", "Follow-me link", "Game", "Video link", "Download link", "Contact email"] + list(user_set))

        for video in video_set:
            ratings = []
            for user in user_set:
                if (user.id, video.id) in d:
                    ratings.append(d[(user.id, video.id)])
                else:
                    ratings.append(None)
            writer.writerow([video.author_name, video.follow_me_link, video.game, video.video_link, video.video_download_link, video.contact_email] + ratings)

        return response

    def test_func(self):
        return self.request.user.is_staff