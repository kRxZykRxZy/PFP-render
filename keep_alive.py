from threading import Thread
import random
import os
import base64
import requests
import zipfile
from flask import Flask, request, jsonify, send_file
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

# GitHub config
GITHUB_USER = 'kRxZykRxZy'
REPO_NAME = 'Project-DB'
GITHUB_API_BASE = f'https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents'
GITHUB_TOKEN = os.getenv('GH_KEY')

if not GITHUB_TOKEN:
    raise EnvironmentError("Missing GH_KEY environment variable.")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Local uploads folder (for fallback or zip route)
LOCAL_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)

@app.route('/upload/compiler', methods=['POST'])
def upload_compiler():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = file.filename
    file_contents = file.read()
    encoded = base64.b64encode(file_contents).decode('utf-8')

    api_url = f"{GITHUB_API_BASE}/{filename}"

    # Check if the file already exists (so we can get the SHA)
    existing = requests.get(api_url, headers=HEADERS)
    sha = existing.json().get('sha') if existing.status_code == 200 else None

    payload = {
        "message": f"Upload {filename} at {datetime.utcnow().isoformat()}",
        "content": encoded,
        "branch": "main"
    }

    if sha:
        payload['sha'] = sha

    response = requests.put(api_url, headers=HEADERS, json=payload)

    if response.status_code in [200, 201]:
        return jsonify({"status": "success", "github_response": response.json()})
    else:
        return jsonify({"status": "failed", "error": response.json()}), response.status_code

@app.route('/uploads/files', methods=['GET'])
def download_zipped_uploads():
    memory_file = BytesIO()

    with zipfile.ZipFile(memory_file, 'w') as zipf:
        for root, _, files in os.walk(LOCAL_UPLOAD_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, LOCAL_UPLOAD_DIR)
                zipf.write(full_path, arcname)

    memory_file.seek(0)
    return send_file(
        memory_file,
        download_name='uploads.zip',
        as_attachment=True,
        mimetype='application/zip'
    )

def run():
  app.run(
    host='0.0.0.0'
  )

def keep_alive():
  '''
  Creates and starts new thread that runs the function run.
  '''
  t = Thread(target=run)
  t.start()
