import os
import base64
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

SSH_KEY_FOLDER = "/root/.ssh"
SSH_KEY_PATH = SSH_KEY_FOLDER + "/id_rsa"
KNOWN_HOSTS_PATH = SSH_KEY_FOLDER+  "/known_hosts"
CLONE_BASE_PATH = "/tmp/repos"

def setup_ssh_key():
    """Writes the SSH key from an environment variable to a file with correct permissions."""
    ssh_key_base64 = os.getenv("GITHUB_SSH_KEY")
    if not ssh_key_base64:
        raise ValueError("GITHUB_SSH_KEY environment variable is missing.")

    # Decode the Base64 key correctly
    ssh_key = base64.b64decode(ssh_key_base64).decode("utf-8").strip()

    os.makedirs(SSH_KEY_FOLDER, exist_ok=True)

    with open(SSH_KEY_PATH, "w") as f:
        f.write(ssh_key + "\n")  # Ensure a newline at the end
    
    with open(KNOWN_HOSTS_PATH, "w") as f:
        f.write("")

    os.chmod(SSH_KEY_PATH, 0o600)

    # Add GitHub to known_hosts
    subprocess.run(["ssh-keyscan", "-t", "rsa", "github.com"], stdout=open(KNOWN_HOSTS_PATH, "w"))

@app.route("/clone", methods=["POST"])
def clone_repo():
    """Clones a given GitHub repo via SSH."""
    data = request.json
    repo_url = data.get("url")

    if not repo_url or not repo_url.startswith("git@github.com:"):
        return jsonify({"error": "Invalid or missing repo_url. Use SSH format."}), 400

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    clone_path = os.path.join(CLONE_BASE_PATH, repo_name)

    setup_ssh_key()

    try:
        subprocess.run(["rm", "-drf", clone_path], check=True)
        subprocess.run(["git", "clone", repo_url, clone_path], check=True)
        return jsonify({"message": f"Repository cloned successfully!", "path": clone_path})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to clone repo: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
