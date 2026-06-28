from django.db import models


class Repository(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, unique=True)
    url = models.URLField()

    def __str__(self):
        return self.full_name


class Commit(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="commits")
    commit_id = models.CharField(max_length=255, unique=True)
    message = models.TextField()
    author = models.CharField(max_length=255)
    timestamp = models.DateTimeField()

    def __str__(self):
        return self.commit_id


class FileChange(models.Model):
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name="files")
    filename = models.CharField(max_length=512)
    status = models.CharField(max_length=50)  # added / modified / removed
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)

    def __str__(self):
        return self.filename