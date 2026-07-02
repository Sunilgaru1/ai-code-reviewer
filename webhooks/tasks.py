import logging

from celery import shared_task
from django.db import transaction

from .models import Repository, WebhookEvent, Commit, FileChange
from .github_api import get_installation_access_token, get_file_content
from .analyzer import analyze_python_code

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_github_webhook(self, event_type, payload):
    if event_type != "push":
        logger.info(f"Ignored event type: {event_type}")
        return f"Ignored event type: {event_type}"

    # Check if this webhook came from a GitHub App installation
    installation_id = payload.get("installation", {}).get("id")
    if not installation_id:
        return "No installation ID found. Is the GitHub App installed correctly?"

    files_to_download = []

    try:
        # FAST DATABASE OPERATIONS
        with transaction.atomic():
            repo_data = payload.get("repository", {})
            commits_data = payload.get("commits", [])

            repo, _ = Repository.objects.get_or_create(
                full_name=repo_data.get("full_name"),
                defaults={
                    "name": repo_data.get("name"),
                    "url": repo_data.get("html_url"),
                    "github_id": repo_data.get("id"),
                },
            )

            event = WebhookEvent.objects.create(
                repository=repo,
                event_type=event_type,
                payload=payload,
                processed=True,
            )

            files_to_save_at_once = []

            for c in commits_data:
                commit_obj, created = Commit.objects.get_or_create(
                    commit_id=c.get("id"),
                    defaults={
                        "repo": repo,
                        "event": event,
                        "message": c.get("message", ""),
                        "author": (c.get("author") or {}).get("name", "unknown"),
                        "timestamp": c.get("timestamp"),
                    },
                )

                if created:
                    # Added files
                    for filename in c.get("added", []):
                        files_to_save_at_once.append(
                            FileChange(
                                commit=commit_obj,
                                filename=filename,
                                status="added",
                            )
                        )
                        files_to_download.append((filename, commit_obj.commit_id))

                    # Modified files
                    for filename in c.get("modified", []):
                        files_to_save_at_once.append(
                            FileChange(
                                commit=commit_obj,
                                filename=filename,
                                status="modified",
                            )
                        )
                        files_to_download.append((filename, commit_obj.commit_id))

                    # Removed files
                    for filename in c.get("removed", []):
                        files_to_save_at_once.append(
                            FileChange(
                                commit=commit_obj,
                                filename=filename,
                                status="removed",
                            )
                        )

            if files_to_save_at_once:
                FileChange.objects.bulk_create(files_to_save_at_once)
                logger.info(
                    f"Bulk created {len(files_to_save_at_once)} file changes."
                )

        # SLOW NETWORK OPERATIONS

        if files_to_download:

            access_token = get_installation_access_token(installation_id)

            if not access_token:
                logger.error("Failed to acquire GitHub Access Token.")
                return "Failed to acquire Access Token."

            logger.info(
                "Successfully acquired GitHub Access Token. Downloading files..."
            )

            for filename, commit_sha in files_to_download:

                code = get_file_content(
                    repo.full_name,
                    filename,
                    commit_sha,
                    access_token,
                )

                if code:
                    logger.info(f"SUCCESS: Read {filename}")

                    # Analyze only Python files
                    if filename.endswith(".py"):

                        metrics = analyze_python_code(code)

                        logger.info(
                            f"AST Metrics for {filename}: {metrics}"
                        )

                    else:
                        logger.info(
                            f"Skipped AST analysis for non-Python file: {filename}"
                        )

        success_msg = (
            f"Successfully processed {len(commits_data)} commits for {repo.name}"
        )

        logger.info(success_msg)

        return success_msg

    except Exception as exc:
        logger.exception("Error processing webhook.")
        raise self.retry(exc=exc)