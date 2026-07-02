import time
import jwt
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def generate_jwt():
    """
    Step 1: Creates the temporary 'ID Card' using our Private Key.
    """
    # Open and read the .pem file you downloaded
    try:
        with open('github_private_key.pem', 'r') as key_file:
            private_key = key_file.read()
    except FileNotFoundError:
        logger.error("Could not find github_private_key.pem!")
        return None

    # This payload tells GitHub who we are and when this ID card expires(10 minutes)
    payload = {
        'iat': int(time.time()),
        'exp': int(time.time()) + (10 * 60),
        'iss': settings.GITHUB_APP_ID
    }

    # We sign it using RS256 (The cryptographic math GitHub requires)
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
    


import base64

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