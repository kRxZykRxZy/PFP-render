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

# Local uploads folder
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

    # Check if the file exists to get SHA
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

    try:
        github_list = requests.get(GITHUB_API_BASE, headers=HEADERS).json()

        if isinstance(github_list, dict) and github_list.get("message"):
            return jsonify({"error": github_list["message"]}), 500

        with zipfile.ZipFile(memory_file, 'w') as zipf:
            for file_info in github_list:
                name = file_info.get('name', '')
                if name.endswith('.sb3') and file_info.get('download_url'):
                    log_name = name
                    file_api_url = file_info['url']
                    file_data = requests.get(file_api_url, headers=HEADERS).json()

                    if file_data.get('encoding') == 'base64':
                        content = base64.b64decode(file_data['content'])
                        zipf.writestr(name, content)
                    else:
                        print(f"[warn] Skipped {log_name}: Not base64 encoded")

        memory_file.seek(0)
        return send_file(
            memory_file,
            download_name='uploads.zip',
            as_attachment=True,
            mimetype='application/zip'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run():
    app.run(
        host='0.0.0.0'
    )

def keep_alive():
    t = Thread(target=run)
    t.start()
