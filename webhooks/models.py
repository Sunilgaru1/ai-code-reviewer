from django.db import models

class Repository(models.Model):
    github_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    url = models.URLField()
    owner = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

class WebhookEvent(models.Model):
    EVENT_TYPES = (
        ('push', 'Push'),
        ('pull_request', 'Pull Request'),
        ('ping', 'Ping'),
    )
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.event_type} on {self.repository.name}"

class Commit(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='commits')
    event = models.ForeignKey(WebhookEvent, on_delete=models.SET_NULL, null=True, blank=True)
    commit_id = models.CharField(max_length=40, unique=True)
    message = models.TextField()
    author = models.CharField(max_length=255)
    timestamp = models.DateTimeField()

    def __str__(self):
        return self.commit_id[:7]

class FileChange(models.Model):
    STATUS_CHOICES = (
        ('added', 'Added'),
        ('modified', 'Modified'),
        ('removed', 'Removed'),
    )
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.filename} ({self.status})"