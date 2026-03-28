import requests
import base64
import time
import os
import urllib3
from config.env_loader import get_env

# Disable SSL warnings (IMPORTANT for ArgoCD HTTPS)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = get_env()


# -----------------------------
# WAIT FOR ARGOCD
# -----------------------------
def wait_for_argocd(url):

    print("\n⏳ Waiting for ArgoCD...\n")

    for i in range(30):
        try:
            r = requests.get(url, timeout=5, verify=False)

            # 200 OR redirect (ArgoCD gives 307)
            if r.status_code in [200, 307]:
                print("✅ ArgoCD Ready")
                return
        except Exception:
            pass

        print(f"Waiting... ({i+1}/30)")
        time.sleep(10)

    raise Exception("❌ ArgoCD not reachable")


# -----------------------------
# GET INITIAL PASSWORD
# -----------------------------
def get_initial_password():

    print("\n🔑 Getting initial admin password...\n")

    cmd = "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}'"
    encoded = os.popen(cmd).read().strip().replace("'", "")

    password = base64.b64decode(encoded).decode("utf-8")

    print("✅ Initial password fetched")
    return password


# -----------------------------
# LOGIN
# -----------------------------
def login(url, password):

    r = requests.post(
        f"{url}/api/v1/session",
        json={
            "username": config["ARGOCD_USER"],
            "password": password
        },
        verify=False
    )

    if r.status_code != 200:
        raise Exception(f"❌ ArgoCD login failed: {r.text}")

    return r.json()["token"]


# -----------------------------
# ENSURE PASSWORD
# -----------------------------
def ensure_password(url):

    print("\n🔐 Ensuring ArgoCD password...\n")

    # Try login with new password first
    test = requests.post(
        f"{url}/api/v1/session",
        json={
            "username": config["ARGOCD_USER"],
            "password": config["ARGOCD_NEW_PASSWORD"]
        },
        verify=False
    )

    if test.status_code == 200:
        print("✅ Password already set")
        return test.json()["token"]

    # Otherwise use initial password
    initial_pwd = get_initial_password()
    token = login(url, initial_pwd)

    headers = {"Authorization": f"Bearer {token}"}

    r = requests.put(
        f"{url}/api/v1/account/password",
        headers=headers,
        json={
            "currentPassword": initial_pwd,
            "newPassword": config["ARGOCD_NEW_PASSWORD"]
        },
        verify=False
    )

    if r.status_code not in [200, 204]:
        raise Exception(f"❌ Password change failed: {r.text}")

    print("✅ Password updated")

    return login(url, config["ARGOCD_NEW_PASSWORD"])


# -----------------------------
# CHECK APP EXISTS
# -----------------------------
def app_exists(url, token, name):

    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(
        f"{url}/api/v1/applications/{name}",
        headers=headers,
        verify=False
    )

    return r.status_code == 200


# -----------------------------
# CREATE APPLICATION
# -----------------------------
def create_app(url, token, name, repo):

    if app_exists(url, token, name):
        print(f"✅ {name} already exists")
        return

    print(f"🚀 Creating app: {name}")

    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "metadata": {"name": name},
        "spec": {
            "project": "default",
            "source": {
                "repoURL": repo,
                "targetRevision": "main",
                "path": "."
            },
            "destination": {
                "server": "https://kubernetes.default.svc",
                "namespace": "default"
            },
            "syncPolicy": {
                "automated": {
                    "prune": True,
                    "selfHeal": True
                }
            }
        }
    }

    r = requests.post(
        f"{url}/api/v1/applications",
        headers=headers,
        json=payload,
        verify=False
    )

    if r.status_code in [200, 201]:
        print(f"✅ {name} created")
    else:
        raise Exception(f"❌ Failed to create {name}: {r.text}")


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def setup_argocd():

    print("\n🚀 ARGOCD CONFIGURATION STARTED\n")

    url = config["ARGOCD_URL"]   

    wait_for_argocd(url)

    token = ensure_password(url)

    create_app(
        url,
        token,
        "java-app",
        "https://github.com/yogithak25/devops-project-k8s-manifests.git"
    )

    create_app(
        url,
        token,
        "python-app",
        "https://github.com/yogithak25/python-devops-k8s-manifests.git"
    )

    print("\n✅ ArgoCD FULLY CONFIGURED SUCCESSFULLY\n")
