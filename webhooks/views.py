from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def github_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    payload = json.loads(request.body)

    event_type = request.headers.get("X-GitHub-Event", "unknown")
    print("=" * 50)
    print(f"Received GitHub event: {event_type}")
    print(f"Repo: {payload.get('repository', {}).get('full_name')}")

    if event_type == "push":
        print(f"Pusher: {payload.get('pusher', {}).get('name')}")
        print(f"Commits: {len(payload.get('commits', []))}")

    print("=" * 50)

    return JsonResponse({"status": "received"}, status=200)