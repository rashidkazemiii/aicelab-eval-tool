"""Upload the app to a private Hugging Face Space.

Before the first run (only once):
    pip install huggingface_hub
    hf auth login
        (paste a token with "Write" access from huggingface.co/settings/tokens)

Then, from the Eval_Tool folder:
    python deploy/huggingface/upload_to_huggingface.py

Run it again whenever you change the app. The Space rebuilds by itself.

Only the code is uploaded. The database (tribology.db), the test data in
backend/data and the trained AI model stay on this PC.
"""
import os

from huggingface_hub import CommitOperationAdd, HfApi

# The Space will be at huggingface.co/spaces/<your user name>/<SPACE_NAME>
SPACE_NAME = "icelab-eval-tool"

DEPLOY_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_FOLDER = os.path.dirname(os.path.dirname(DEPLOY_FOLDER))

# Files from deploy/huggingface/ that go to the top level of the Space.
DEPLOY_FILES = ["Dockerfile", "requirements.txt", "README.md"]

# Single files from the project (same path inside the Space).
APP_FILES = [
    "app.py",
    "pyproject.toml",
    "backend/raw_data_settings.json",
    "backend/templates/summary_template.xlsx",
]

# Folders whose .py files are uploaded (subfolders are not included).
CODE_FOLDERS = ["backend", "backend/physics"]


def collect_files():
    """A list of "add this file" steps for one upload."""
    operations = []

    for name in DEPLOY_FILES:
        local_path = os.path.join(DEPLOY_FOLDER, name)
        operations.append(CommitOperationAdd(path_in_repo=name, path_or_fileobj=local_path))

    for relative_path in APP_FILES:
        local_path = os.path.join(PROJECT_FOLDER, relative_path)
        operations.append(CommitOperationAdd(path_in_repo=relative_path, path_or_fileobj=local_path))

    for folder in CODE_FOLDERS:
        folder_path = os.path.join(PROJECT_FOLDER, folder)
        for name in sorted(os.listdir(folder_path)):
            if not name.endswith(".py"):
                continue
            local_path = os.path.join(folder_path, name)
            operations.append(CommitOperationAdd(path_in_repo=folder + "/" + name, path_or_fileobj=local_path))

    return operations


def main():
    api = HfApi()

    try:
        user_name = api.whoami()["name"]
    except Exception:
        print("You are not logged in to Hugging Face. Run:  hf auth login")
        return

    repo_id = user_name + "/" + SPACE_NAME

    # Creates the private Space the first time; does nothing if it exists.
    api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker", private=True, exist_ok=True)

    operations = collect_files()
    print("Uploading " + str(len(operations)) + " files to " + repo_id + " ...")
    for operation in operations:
        print("  " + operation.path_in_repo)

    api.create_commit(
        repo_id=repo_id,
        repo_type="space",
        operations=operations,
        commit_message="Update app",
    )

    print("Done. The Space is building now (takes a few minutes):")
    print("  https://huggingface.co/spaces/" + repo_id)


if __name__ == "__main__":
    main()
