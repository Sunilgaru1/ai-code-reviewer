import json
import hmac
import hashlib
import pytest
from django.conf import settings
from unittest.mock import patch
from django.urls import reverse
from webhooks.github_api import generate_jwt

# We removed @pytest.mark.django_db here so Pytest doesn't try to build a database!
def test_github_webhook_push_event(client):
    """
    Simulates a GitHub 'push' event to ensure our webhook endpoint securely 
    accepts the payload and triggers the Celery worker.
    """
    
    # 1. Create a fake GitHub Payload
    fake_payload = {
        "repository": {
            "id": 12345,
            "name": "ai-code-reviewer",
            "full_name": "Sunilgaru1/ai-code-reviewer",
            "html_url": "https://github.com/Sunilgaru1/ai-code-reviewer"
        },
        "commits": [
            {
                "id": "fake_commit_123",
                "message": "Automated test commit",
                "author": {"name": "Sunil"},
                "added": ["messy_code.py"],
                "modified": [],
                "removed": []
            }
        ],
        "installation": {"id": 999999}
    }

    # Convert the Python dictionary into raw JSON bytes
    payload_bytes = json.dumps(fake_payload).encode('utf-8')

    # 2. Forge the VIP Signature (Act exactly like GitHub)
    secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", "").encode('utf-8')
    mac = hmac.new(secret, msg=payload_bytes, digestmod=hashlib.sha256)
    fake_signature = f"sha256={mac.hexdigest()}"

    # 3. Use 'patch' to intercept the Celery task so we don't actually call Gemini during a quick test
    with patch('webhooks.views.process_github_webhook.delay') as mock_celery_task:
        
        # 4. Fire the fake payload at our Django app!
        response = client.post(
            reverse('github_webhook'), 
            data=payload_bytes,
            content_type='application/json',
            HTTP_X_GITHUB_EVENT='push',
            HTTP_X_HUB_SIGNATURE_256=fake_signature
        )

        # 5. Assertions (Did the system react the way we expect?)
        assert response.status_code == 202
        assert response.json() == {"status": "Task queued successfully"}
        
        # Prove that Django successfully parsed the data and handed it to Celery
        mock_celery_task.assert_called_once_with('push', fake_payload)


def test_generate_jwt_uses_environment_private_key(monkeypatch):
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "fake-private-key")
    monkeypatch.delenv("GITHUB_PRIVATE_KEY_PATH", raising=False)

    with patch.object(settings, "GITHUB_APP_ID", "12345"), patch("webhooks.github_api.jwt.encode", return_value="test-token") as mock_encode:
        token = generate_jwt()

    assert token == "test-token"
    assert mock_encode.call_args.args[1] == "fake-private-key"
    assert mock_encode.call_args.args[0]["iss"] == "12345"