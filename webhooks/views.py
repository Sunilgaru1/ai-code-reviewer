import hmac
import hashlib
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tasks import process_github_webhook

def verify_signature(request):
    """The Bouncer: Checks if the request actually came from GitHub."""
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        return False

    sha_name, signature = signature_header.split("=")
    if sha_name != "sha256":
        return False

    # Grabs your secret password from settings.py
    secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", "").encode("utf-8")
    
    # Does the math
    mac = hmac.new(secret, msg=request.body, digestmod=hashlib.sha256)
    
    # Compares our math answer with GitHub's math answer
    return hmac.compare_digest(mac.hexdigest(), signature)

@csrf_exempt
def github_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    # Security Check! If the math doesn't match, kick them out.
    if not verify_signature(request):
        return JsonResponse({"error": "Invalid signature."}, status=403)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    event_type = request.headers.get("X-GitHub-Event", "push")

    # Send to the Back-Office (Celery)
    process_github_webhook.delay(event_type, payload)

    return JsonResponse({"status": "Task queued successfully"}, status=202)