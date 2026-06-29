import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tasks import process_github_webhook # Import the worker!

@csrf_exempt
def github_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    event_type = request.headers.get("X-GitHub-Event", "push")

    process_github_webhook.delay(event_type, payload)
    return JsonResponse({"status": "Task queued successfully"}, status=202)