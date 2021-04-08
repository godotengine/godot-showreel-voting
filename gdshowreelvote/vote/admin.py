from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Video, Vote, Showreel

class ShowreelAdmin(admin.ModelAdmin):
    list_display = ('title', 'status' , 'results')

    def results(self, showreel):
        return format_html("<a href={}>CSV</a>", reverse('csv-results', args=[showreel.id]))

admin.site.register(Showreel, ShowreelAdmin)
admin.site.register(Video)
admin.site.register(Vote)
