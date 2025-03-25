import os
import shutil
import subprocess
import tempfile
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/clone", methods=["POST"])
def clone_repo():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url' in request"}), 400

    repo_url = data["url"]
    
    # Ensure the URL is in SSH format
    if not repo_url.startswith("git@github.com:"):
        return jsonify({"error": "Repository URL must be in SSH format (git@github.com:username/repo.git)"}), 400

    # Create a temporary directory to clone the repo
    temp_dir = tempfile.mkdtemp()

    try:
        # Set SSH key permissions and environment variable
        os.environ["GIT_SSH_COMMAND"] = "ssh -i /root/.ssh/id_rsa -o StrictHostKeyChecking=no"

        # Clone the repo using SSH
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
   
        # Get a list of files in the cloned repo
        files = []
        for root, _, filenames in os.walk(temp_dir):
            for filename in filenames:
                files.append(os.path.relpath(os.path.join(root, filename), temp_dir))

        return jsonify({"repo_url": repo_url, "files": files})

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Failed to clone repository", "details": str(e)}), 500

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
