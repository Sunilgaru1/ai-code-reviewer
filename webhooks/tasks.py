from celery import shared_task
from django.db import transaction
from .models import Repository, WebhookEvent, Commit, FileChange

@shared_task
def process_github_webhook(event_type, payload):
    # If it's not a push, we just ignore it for now
    if event_type != 'push':
        return f"Ignored event type: {event_type}"

    # transaction.atomic() means "if something crashes, undo everything so the database isn't corrupted"
    with transaction.atomic():
        repo_data = payload.get('repository', {})
        commits_data = payload.get('commits', [])
        
        # Save or get repository
        repo, _ = Repository.objects.get_or_create(
            full_name=repo_data.get('full_name'),
            defaults={
                'name': repo_data.get('name'),
                'url': repo_data.get('html_url'),
                'github_id': repo_data.get('id'),
            }
        )

        # Save the Webhook Event history
        event = WebhookEvent.objects.create(
            repository=repo,
            event_type=event_type,
            payload=payload,
            processed=True
        )

        # Process commits and their files
        for c in commits_data:
            commit_obj, created = Commit.objects.get_or_create(
                commit_id=c.get('id'),
                defaults={
                    'repo': repo,
                    'event': event,
                    'message': c.get('message', ''),
                    'author': (c.get('author') or {}).get('name', 'unknown'),
                    'timestamp': c.get('timestamp'),
                }
            )

            # Process files in commit (Only if the commit is brand new)
            if created:
                for f in c.get("added", []):
                    FileChange.objects.create(commit=commit_obj, filename=f, status="added")
                for f in c.get("modified", []):
                    FileChange.objects.create(commit=commit_obj, filename=f, status="modified")
                for f in c.get("removed", []):
                    FileChange.objects.create(commit=commit_obj, filename=f, status="removed")
    
    return f"Successfully processed {len(commits_data)} commits for {repo.name}"