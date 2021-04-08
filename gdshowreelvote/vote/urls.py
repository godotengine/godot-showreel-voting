from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.VoteView.as_view(), name="vote"),
    path('vote/delete-last', views.LastVoteDeleteView.as_view(), name="delete-last-vote"),
    path('submissions', views.UserVideoListView.as_view(), name="submissions"),
    path('submissions/new', views.VideoCreateView.as_view(), name="new-submission"),
    path('submissions/<int:pk>/delete', views.VideoDeleteView.as_view(), name="delete-submission"),
    path('submissions/<int:pk>/update', views.VideoUpdateView.as_view(), name="update-submission"),

    path('showreel/<int:pk>/csvresults', views.ShowreelResultsAsCSVView.as_view(), name='csv-results'),

    path('about', views.AboutView.as_view(), name="about"),
]


