import logging
from celery import shared_task
from django.db import transaction
from .models import Repository, WebhookEvent, Commit, FileChange
from .github_api import get_installation_access_token, get_file_content # NEW IMPORTS

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_github_webhook(self, event_type, payload):
    if event_type != 'push':
        logger.info(f"Ignored event type: {event_type}")
        return f"Ignored event type: {event_type}"

    # 1. Check if this webhook came from a GitHub App installation
    installation_id = payload.get('installation', {}).get('id')
    if not installation_id:
        return "No installation ID found. Is the GitHub App installed correctly?"

    # We need to save a list of the files we want to download later
    files_to_download = []

    try:
        # THE PROTECTIVE BUBBLE (Fast database stuff only)
        with transaction.atomic():
            repo_data = payload.get('repository', {})
            commits_data = payload.get('commits', [])
            
            repo, _ = Repository.objects.get_or_create(
                full_name=repo_data.get('full_name'),
                defaults={
                    'name': repo_data.get('name'),
                    'url': repo_data.get('html_url'),
                    'github_id': repo_data.get('id'),
                }
            )

            event = WebhookEvent.objects.create(
                repository=repo, event_type=event_type, payload=payload, processed=True
            )

            files_to_save_at_once = []

            for c in commits_data:
                commit_obj, created = Commit.objects.get_or_create(
                    commit_id=c.get('id'),
                    defaults={
                        'repo': repo, 'event': event, 'message': c.get('message', ''),
                        'author': (c.get('author') or {}).get('name', 'unknown'),
                        'timestamp': c.get('timestamp'),
                    }
                )

                if created:
                    # Save to DB tray AND add to our download list
                    for f in c.get("added", []):
                        files_to_save_at_once.append(FileChange(commit=commit_obj, filename=f, status="added"))
                        files_to_download.append((f, commit_obj.commit_id)) # We need the filename and the commit ID
                        
                    for f in c.get("modified", []):
                        files_to_save_at_once.append(FileChange(commit=commit_obj, filename=f, status="modified"))
                        files_to_download.append((f, commit_obj.commit_id))

                    for f in c.get("removed", []):
                        files_to_save_at_once.append(FileChange(commit=commit_obj, filename=f, status="removed"))
                        # We don't download removed files because they don't exist anymore!
            
            if files_to_save_at_once:
                FileChange.objects.bulk_create(files_to_save_at_once)
                logger.info(f"Bulk created {len(files_to_save_at_once)} file changes.")

        # ==========================================
        # OUTSIDE THE BUBBLE (Slow internet stuff)
        # ==========================================
        
        # If there are files to download, let's get our VIP Wristband
        if files_to_download:
            access_token = get_installation_access_token(installation_id)
            
            if access_token:
                logger.info("Successfully acquired GitHub Access Token. Downloading files...")
                for filename, commit_sha in files_to_download:
                    code = get_file_content(repo.full_name, filename, commit_sha, access_token)
                    if code:
                        # For right now, we will just print the first 100 characters to the Celery log to prove it works!
                        logger.info(f"SUCCESS: Read {filename} -> {code[:100]}...")
            else:
                logger.error("Failed to acquire Access Token. Cannot download code.")

        success_msg = f"Successfully processed {len(commits_data)} commits for {repo.name}"
        return success_msg

    except Exception as exc:
        logger.error(f"Error processing webhook: {exc}. Retrying...")
        raise self.retry(exc=exc)