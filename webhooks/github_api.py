import os
import time
import jwt
import requests
from django.conf import settings
import logging
import base64

logger = logging.getLogger(__name__)

def load_private_key():
    private_key = os.getenv("GITHUB_PRIVATE_KEY")
    if private_key:
        return private_key

    key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH", str(settings.BASE_DIR / 'github_private_key.pem'))

    try:
        with open(key_path, 'r') as key_file:
            return key_file.read()
    except FileNotFoundError:
        logger.error(f"Could not find private key at exactly: {key_path}")
        return None


def generate_jwt():
    """
    Step 1: Creates the temporary 'ID Card' using our Private Key.
    """
    private_key = load_private_key()
    if not private_key:
        return None

    payload = {
        'iat': int(time.time()),
        'exp': int(time.time()) + (5* 60),
        'iss': settings.GITHUB_APP_ID
    }

    encoded_jwt = jwt.encode(payload, private_key, algorithm='RS256')
    return encoded_jwt

def get_installation_access_token(installation_id):
    """
    Step 2: Trades our 'ID Card' for a 1-hour 'VIP Wristband' to read the code.
    """
    jwt_token = generate_jwt()
    if not jwt_token:
        return None

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 201:
        # Success!! We got the wristband.
        return response.json().get("token")
    else:
        logger.error(f"Failed to get access token: {response.text}")
        return None
    


def get_file_content(repo_full_name, filename, commit_sha, access_token):
    """
    Step 3: Uses the VIP Wristband to download the actual code of a single file.
    """
    # We ask GitHub for the specific file at the exact moment of this commit
    url = f"https://api.github.com/repos/{repo_full_name}/contents/{filename}?ref={commit_sha}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        
        # GitHub gives us 'content' in Base64. We decode it into raw bytes, then into a readable utf-8 string.
        raw_bytes = base64.b64decode(data['content'])
        readable_code = raw_bytes.decode('utf-8')
        
        return readable_code
    else:
        logger.error(f"Failed to fetch {filename}: {response.text}")
        return None
    
def post_github_comment(repo_full_name, commit_sha, access_token, comment_body):
    """
    Step 4: Uses the VIP Wristband to post our AI review directly as a comment on the GitHub commit.
    """
    url = f"https://api.github.com/repos/{repo_full_name}/commits/{commit_sha}/comments"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "body": comment_body
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        logger.info(f"Successfully posted AI Review to GitHub commit: {commit_sha}")
        return True
    else:
        logger.error(f"Failed to post comment to GitHub: {response.text}")
        return False