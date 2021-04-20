from urllib.parse import urlparse, parse_qs

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import TemplateView
from django.views import View
from django.urls import reverse_lazy
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

    def _youtube_video_id(self, value):
        query = urlparse(value)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        return None

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.video = self._get_not_rated_video()
        obj.save()
        return super(VoteView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        video = self._get_not_rated_video()
        if video:
            context["video"] = video
            youtuber_video_id =  self._youtube_video_id(video.video_link)
            if youtuber_video_id:
                context["youtube_video_id"] = youtuber_video_id

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

# Display the list of a user's submissions
class UserVideoListView(LoginRequiredMixin, ListView):
    model = Video

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

# Display the about page
class AboutView(LoginRequiredMixin, TemplateView):
    template_name = "vote/about.html"

# Download a csv of a showreel results
class ShowreelResultsAsCSVView(LoginRequiredMixin, UserPassesTestMixin, SingleObjectMixin, View):
    model=Showreel

    def get(self, request, *args, **kwargs):
        # Create the HttpResponse object with the appropriate CSV header.

        showreel = self.get_object()

        votes = Vote.objects.filter(video__showreel=showreel).select_related('video', 'user')
        video_set = votes.values_list('video', flat=True).distinct()
        video_set = Video.objects.filter(id__in=video_set)
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
        writer.writerow(["Author", "Follow-me link", "Game", "Video link"] + list(user_set))

        for video in video_set:
            ratings = []
            for user in user_set:
                if (user.id, video.id) in d:
                    ratings.append(d[(user.id, video.id)])
                else:
                    ratings.append(None)
            writer.writerow([video.author_name, video.follow_me_link, video.game, video.video_link] + ratings)

        return response

    def test_func(self):
        return self.request.user.is_staff