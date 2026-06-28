from celery import shared_task
from .models import Repository, Commit


@shared_task
def save_webhook_event(payload):
    repo_data = payload.get("repository", {})
    commits = payload.get("commits", [])

    # 1. Get or create repository
    repo, _ = Repository.objects.get_or_create(
        full_name=repo_data.get("full_name"),
        defaults={
            "name": repo_data.get("name", ""),
            "url": repo_data.get("html_url", "")
        }
    )

    # 2. Save commits
    for c in commits:
        Commit.objects.get_or_create(
            repo=repo,
            commit_id=c.get("id"),
            defaults={
                "message": c.get("message", ""),
                "author": (c.get("author") or {}).get("name", "unknown"),
                "timestamp": c.get("timestamp")
            }
        )

    print("Webhook saved to DB successfully!")