import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def github_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event_type = request.headers.get("X-GitHub-Event", "unknown")

    print("=" * 50)
    print(f"Received GitHub event: {event_type}")

    repository = payload.get("repository", {})
    print(f"Repository: {repository.get('full_name')}")

    if event_type == "push":
        pusher = payload.get("pusher", {})
        commits = payload.get("commits", [])

        print(f"Pusher: {pusher.get('name')}")
        print(f"Branch: {payload.get('ref')}")
        print(f"Commits: {len(commits)}")

        for commit in commits:
            print("-" * 30)
            print(f"Message : {commit.get('message')}")
            print(f"Author  : {commit.get('author', {}).get('name')}")
            print(f"Commit  : {commit.get('id')[:7]}")

    print("=" * 50)
    return JsonResponse({"status": "received"})