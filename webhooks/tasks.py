import logging
from celery import shared_task
from django.db import transaction
from .models import Repository, WebhookEvent, Commit, FileChange
from .github_api import get_installation_access_token, get_file_content
from .analyzer import analyze_python_code
from ml_engine.services import get_maintainability_score
from ml_engine.llm_reviewer import generate_code_review
from .github_api import get_installation_access_token, get_file_content, post_github_comment

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
                    # The Brain (AST Parsing + ML Prediction)
                    if filename.endswith(".py"):
                        metrics = analyze_python_code(code)
                        
                        # Grab the AST numbers
                        func_count = metrics.get('functions', 0)
                        class_count = metrics.get('classes', 0)
                        loop_count = metrics.get('loops', 0)
                        comp_score = metrics.get('complexity', 1)
                        
                        # Ask the ML Engine for a grade
                        ai_score = get_maintainability_score(func_count, class_count, loop_count, comp_score)

                        logger.info(f"AST Metrics: {metrics} | AI Maintainability Score: {ai_score}/100")

                        # NEW: Tier 2 Generative AI Review
                        # If the code smells (let's say under 90 for testing purposes), trigger the LLM
                        if ai_score < 90.0:
                            logger.info(f"Score below threshold. Triggering LLM Code Review for {filename}...")
                            review_markdown = generate_code_review(filename, code, metrics, ai_score)

                            if review_markdown:
                                # Add a nice header to the bot's comment
                                final_comment = f"🤖 **AI Code Reviewer Boat**\n\n{review_markdown}"
                                post_github_comment(repo.full_name, commit_sha, access_token, final_comment)

                        # Save everything permanently to the Database
                        FileChange.objects.filter(
                            commit__commit_id=commit_sha, 
                            filename=filename
                        ).update(
                            functions_count=func_count,
                            classes_count=class_count,
                            loops_count=loop_count,
                            complexity_score=comp_score,
                            maintainability_score=ai_score
                        )
                    
                    else:
                        logger.info(f"Skipped AST analysis for non-Python file: {filename}")

        success_msg = (
            f"Successfully processed {len(commits_data)} commits for {repo.name}"
        )

        logger.info(success_msg)

        return success_msg

    except Exception as exc:
        logger.exception("Error processing webhook.")
        raise self.retry(exc=exc)