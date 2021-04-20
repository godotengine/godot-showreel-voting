from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import ugettext_lazy as _

from vote.models import User

from .models import Video, Vote, Showreel

class ShowreelAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'results')

    def results(self, showreel):
        return format_html("<a href={}>CSV</a>", reverse('csv-results', args=[showreel.id]))

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(Showreel, ShowreelAdmin)
admin.site.register(Video)
admin.site.register(Vote)
admin.site.register(User, UserAdmin)
