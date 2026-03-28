import requests
from config.env_loader import get_env

config = get_env()


# -----------------------------
# COMMON HEADERS
# -----------------------------
def headers():
    return {
        "Authorization": f"token {config['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json"
    }


# -----------------------------
# CHECK WEBHOOK EXISTS
# -----------------------------
def webhook_exists(repo):

    url = f"https://api.github.com/repos/{config['GITHUB_USER']}/{repo}/hooks"

    r = requests.get(url, headers=headers())

    if r.status_code != 200:
        print(f"❌ Failed to fetch hooks for {repo}")
        return False

    hooks = r.json()

    jenkins_url = f"{config['JENKINS_URL']}/github-webhook/"

    for hook in hooks:
        if hook["config"].get("url") == jenkins_url:
            return True

    return False


# -----------------------------
# CREATE WEBHOOK
# -----------------------------
def create_webhook(repo):

    if webhook_exists(repo):
        print(f"✅ Webhook already exists for {repo}")
        return

    url = f"https://api.github.com/repos/{config['GITHUB_USER']}/{repo}/hooks"

    payload = {
        "name": "web",
        "active": True,
        "events": ["push"],
        "config": {
            "url": f"{config['JENKINS_URL']}/github-webhook/",
            "content_type": "json"
        }
    }

    r = requests.post(url, headers=headers(), json=payload)

    if r.status_code in [200, 201]:
        print(f"✅ Webhook created for {repo}")
    else:
        print(f"❌ Failed to create webhook for {repo}: {r.text}")


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def setup_github():

    print("\n🚀 GITHUB WEBHOOK SETUP STARTED\n")

    repos = [
        "end-to-end-devops-project",       # Java repo
        "python-devops-project"            # Python repo
    ]

    for repo in repos:
        create_webhook(repo)

    print("\n✅ GitHub Webhooks Configured Successfully\n")
