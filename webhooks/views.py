import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Repository, Commit, FileChange


@csrf_exempt
def github_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    payload = json.loads(request.body)

    repo_data = payload.get("repository", {})
    commits = payload.get("commits", [])

    # 1. Save or get repository
    repo, _ = Repository.objects.get_or_create(
        full_name=repo_data.get("full_name"),
        defaults={
            "name": repo_data.get("name"),
            "url": repo_data.get("html_url"),
        }
    )

    # 2. Process commits
    for c in commits:
        commit_obj, created = Commit.objects.get_or_create(
            commit_id=c.get("id"),
            defaults={
                "repo": repo,
                "message": c.get("message", ""),
                "author": (c.get("author") or {}).get("name", "unknown"),
                "timestamp": c.get("timestamp"),
            }
        )

        # 3. Process files in commit
        for f in c.get("added", []):
            FileChange.objects.create(
                commit=commit_obj,
                filename=f,
                status="added"
            )

        for f in c.get("modified", []):
            FileChange.objects.create(
                commit=commit_obj,
                filename=f,
                status="modified"
            )

        for f in c.get("removed", []):
            FileChange.objects.create(
                commit=commit_obj,
                filename=f,
                status="removed"
            )

    return JsonResponse({"status": "stored"})

