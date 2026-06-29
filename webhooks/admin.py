from django.contrib import admin
from .models import Repository, Commit, FileChange,WebhookEvent

admin.site.register(Repository)
admin.site.register(Commit)
admin.site.register(FileChange)
admin.site.register(WebhookEvent)