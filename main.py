import os
import base64
import shutil
import requests
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

SSH_BASE_PATH = "/root/.ssh"
SSH_KEY_PATH = os.path.join(SSH_BASE_PATH, "id_rsa")
SSH_KNOWN_HOSTS_PATH = os.path.join(SSH_BASE_PATH,  "known_hosts")
CLONE_BASE_PATH = "/tmp/repos"
OUTPUT_BASE_PATH = "/mnt/output"
METADATA_BASE_PATH = "/mnt/metadata"

def get_project_number():
    """Retrieves the Google Cloud Project Number from the Metadata Server."""
    metadata_url = "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id"
    headers = {"Metadata-Flavor": "Google"}
    try:
        response = requests.get(metadata_url, headers=headers, timeout=2)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching project number from metadata server: {e}")
        return None

def get_region():
    """Retrieves the Google Cloud Region from the Metadata Server."""
    metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/region"
    headers = {"Metadata-Flavor": "Google"}
    try:
        response = requests.get(metadata_url, headers=headers, timeout=2)
        response.raise_for_status()  # Raise an exception for bad status codes
        region = response.text.split("/")[-1]
        return region
    except requests.exceptions.RequestException as e:
        print(f"Error fetching region from metadata server: {e}")
        return None


def setup_ssh_key():
    """Writes the SSH key from an environment variable to a file with correct permissions."""
    ssh_key_base64 = os.getenv("GITHUB_SSH_KEY")
    if not ssh_key_base64:
        raise ValueError("GITHUB_SSH_KEY environment variable is missing.")

    # Decode the Base64 key correctly
    ssh_key = base64.b64decode(ssh_key_base64).decode("utf-8").strip()

    os.makedirs(SSH_BASE_PATH, exist_ok=True)

    with open(SSH_KEY_PATH, "w") as f:
        f.write(ssh_key + "\n")  # Ensure a newline at the end
    
    with open(SSH_KNOWN_HOSTS_PATH, "w") as f:
        f.write("")

    os.chmod(SSH_KEY_PATH, 0o600)

    # Add GitHub to known_hosts
    subprocess.run(["ssh-keyscan", "-t", "rsa", "github.com"], stdout=open(SSH_KNOWN_HOSTS_PATH, "w"))

def delete_everything_except_git(folder_path):
    """
    Deletes all files and folders within the given folder path,
    except for a folder named '.git'.

    Args:
        folder_path: The path to the folder you want to clean.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at '{folder_path}'")
        return

    for item_name in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item_name)
        if item_name == '.git':
            print(f"Skipping: '{item_name}'")
            continue
        elif os.path.isfile(item_path):
            try:
                os.remove(item_path)
                print(f"Deleted file: '{item_name}'")
            except OSError as e:
                print(f"Error deleting file '{item_name}': {e}")
        elif os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
                print(f"Deleted folder: '{item_name}'")
            except OSError as e:
                print(f"Error deleting folder '{item_name}': {e}")

def copy_contents(source_folder, destination_folder):
    """
    Copies all files and folders from the source folder to the destination folder.

    Args:
        source_folder: The path to the folder containing the items to copy.
        destination_folder: The path to the folder where the items will be copied.
    """
    if not os.path.isdir(source_folder):
        print(f"Error: Source folder not found at '{source_folder}'")
        return
    if not os.path.isdir(destination_folder):
        try:
            os.makedirs(destination_folder)
            print(f"Created destination folder: '{destination_folder}'")
        except OSError as e:
            print(f"Error creating destination folder '{destination_folder}': {e}")
            return

    for item_name in os.listdir(source_folder):
        source_item_path = os.path.join(source_folder, item_name)
        destination_item_path = os.path.join(destination_folder, item_name)
        try:
            shutil.move(source_item_path, destination_item_path)
            print(f"Copied '{item_name}' from '{source_folder}' to '{destination_folder}'")
        except OSError as e:
            print(f"Error coping '{item_name}': {e}")

def create_and_push_git_branch(repo_path, new_branch_name, remote_name='origin'):
    """
    Creates a new Git branch locally and pushes it to a remote repository.

    Args:
        repo_path: The local path to the Git repository.
        new_branch_name: The name of the new branch to create.
        remote_name: The name of the remote repository (default is 'origin').

    Returns:
        True if the operations were successful, False otherwise.
    """
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        print(f"Error: '{repo_path}' is not a valid Git repository.")
        return False

    original_cwd = os.getcwd()
    os.chdir(repo_path)

    try:
        # Config user
        config_user_command = ['git', 'config', '--global', 'user.name', 'Code ETR']
        config_user_process = subprocess.run(config_user_command, capture_output=True, text=True, check=True)
        print(f"User set successfully")
        print(config_user_process.stdout)
        if config_user_process.stderr:
            print(f"Warning (create branch): {config_user_process.stderr}")

        # Config email
        config_email_command = ['git', 'config', '--global', 'user.email', 'code-etr@localhost']
        config_email_process = subprocess.run(config_email_command, capture_output=True, text=True, check=True)
        print(f"Email set successfully")
        print(config_email_process.stdout)
        if config_email_process.stderr:
            print(f"Warning (create branch): {config_email_process.stderr}")


        # Create the new branch locally
        create_branch_command = ['git', 'checkout', '-b', new_branch_name]
        create_process = subprocess.run(create_branch_command, capture_output=True, text=True, check=True)
        print(f"Successfully created local branch: {new_branch_name}")
        print(create_process.stdout)
        if create_process.stderr:
            print(f"Warning (create branch): {create_process.stderr}")

        # Add changes
        add_command = ['git', 'add', '.']
        add_process = subprocess.run(add_command, capture_output=True, text=True, check=True)
        print(f"Successfully added changes to branch '{new_branch_name}'.")
        print(add_process.stdout)
        if add_process.stderr:
            print(f"Warning (add changes): {add_process.stderr}")

         # Commit changes
        commit_command = ['git', 'commit', '-m', '"Changes proposed by Code ETR"']
        commit_process = subprocess.run(commit_command, capture_output=True, text=True, check=True)
        print(f"Successfully committed changes to branch '{new_branch_name}'.")
        print(commit_process.stdout)
        if commit_process.stderr:
            print(f"Warning (commit changes): {commit_process.stderr}")

        # Push the new branch to the remote
        push_command = ['git', 'push', '-u', remote_name, new_branch_name]
        push_process = subprocess.run(push_command, capture_output=True, text=True, check=True)
        print(f"Successfully pushed branch '{new_branch_name}' to remote '{remote_name}'.")
        print(push_process.stdout)
        if push_process.stderr:
            print(f"Warning (push branch): {push_process.stderr}")

        os.chdir(original_cwd)
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error executing Git command: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        os.chdir(original_cwd)
        return False
    except FileNotFoundError:
        print("Error: 'git' command not found. Make sure Git is installed and in your PATH.")
        os.chdir(original_cwd)
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        os.chdir(original_cwd)
        return False


@app.route("/code-etr", methods=["POST"])
def run_code_etr():
    """Clones a given GitHub repo via SSH."""
    data = request.json
    repo_url = data.get("repo_url")

    if not repo_url or not repo_url.startswith("git@github.com:"):
        return jsonify({"error": "Invalid or missing repo_url. Use SSH format."}), 400

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    clone_path = os.path.join(CLONE_BASE_PATH, repo_name)
    setup_ssh_key()

    try:
        subprocess.run(["rm", "-drf", clone_path], check=True)
        subprocess.run(["git", "clone", repo_url, clone_path], check=True)
        print(f"Repository cloned successfully!")
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to clone repo: {e}"}), 500
    except FileNotFoundError:
        return jsonify({"error": f"Failed to clone repo: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to clone repo: {e}"}), 500
    
    repo_output = os.path.join(OUTPUT_BASE_PATH, repo_name)
    if not os.path.exists(repo_output):
        try:
            os.mkdir(repo_output)
            print(f"Folder '{repo_output}' created successfully.")
        except OSError as e:
            print(f"Error creating folder '{repo_output}': {e}")
            return jsonify({"message": f"Error creating folder '{repo_output}': {e}"}), 500
    else:
        print(f"Folder '{repo_output}' already exist.")

    action = data.get("action", "scan")
    output_bucket = "gs://" + os.getenv("OUTPUT_BUCKET") + "/" + repo_name
    project_number = get_project_number()
    metadata_location = os.path.join(METADATA_BASE_PATH, repo_name, "metadata.zip")
    location = get_region()
    try:
        subprocess.run([
            "./code_etr", action,
            "--force",
            "--name", repo_name,
            "--input-path", clone_path,
            "--root-path", output_bucket,
            "--gcp-project-number", project_number,
            "--translate-metadata-file", metadata_location,
            "--gcp-project-location", location
        ], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to run code ETR: {e}"}), 500
    except FileNotFoundError:
        return jsonify({"error": f"Failed to run code ETR: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to run code ETR: {e}"}), 500
    
    return jsonify({"message": f"Code ETR analysis complete!", "output": f'{output_bucket}'})

@app.route("/create-branch", methods=["POST"])
def create_branch():
    """Clones a given GitHub repo via SSH."""
    data = request.json
    repo_url = data.get("repo_url")
    new_branch_name = data.get("new_branch")

    if not repo_url or not repo_url.startswith("git@github.com:"):
        return jsonify({"error": "Invalid or missing repo_url. Use SSH format."}), 400

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    clone_path = os.path.join(CLONE_BASE_PATH, repo_name)
    setup_ssh_key()

    try:
        subprocess.run(["rm", "-drf", clone_path], check=True)
        subprocess.run(["git", "clone", repo_url, clone_path], check=True)
        print(f"Repository cloned successfully!")
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to clone repo: {e}"}), 500
    except FileNotFoundError:
        return jsonify({"error": f"Failed to clone repo: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to clone repo: {e}"}), 500
    
    repo_output = os.path.join(OUTPUT_BASE_PATH, repo_name, 'code_sets', repo_name, 'output')

    generated_git_path = os.path.join(repo_output, '.git')
    if os.path.exists(generated_git_path):
        shutil.rmtree(generated_git_path)

    delete_everything_except_git(clone_path)
    copy_contents(repo_output, clone_path)
    create_and_push_git_branch(clone_path, new_branch_name)

    return jsonify({"message": f"Created {new_branch_name} branch in: {repo_url}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
