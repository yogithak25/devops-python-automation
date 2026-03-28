import os
import time
import requests
from config.env_loader import get_env

config = get_env()

BASE_URL = config["NEXUS_URL"]


# -----------------------------
# WAIT FOR NEXUS
# -----------------------------
def wait_for_nexus():

    print("\n⏳ Waiting for Nexus...\n")

    for i in range(30):
        try:
            r = requests.get(BASE_URL)
            if r.status_code in [200, 401]:
                print("✅ Nexus Ready")
                return
        except:
            pass

        print(f"Waiting... ({i+1}/30)")
        time.sleep(10)

    raise Exception("❌ Nexus not reachable")


# -----------------------------
# GET INITIAL PASSWORD
# -----------------------------
def get_initial_password():

    print("\n🔑 Getting Nexus initial password...\n")

    try:
        with open("/opt/sonatype-work/nexus3/admin.password", "r") as f:
            pwd = f.read().strip()
            print("✅ Initial password fetched")
            return pwd
    except:
        print("ℹ️ Initial password file not found (probably already changed)")
        return None


# -----------------------------
# CHECK PASSWORD ALREADY CHANGED
# -----------------------------
def is_password_changed():

    try:
        r = requests.get(
            f"{BASE_URL}/service/rest/v1/status",
            auth=(config["NEXUS_USER"], config["NEXUS_PASSWORD"])
        )
        return r.status_code == 200
    except:
        return False


# -----------------------------
# CHANGE PASSWORD
# -----------------------------
def change_password(initial_pwd):

    if is_password_changed():
        print("✅ Nexus password already updated. Skipping.")
        return

    print("\n🔐 Changing Nexus password...\n")

    response = requests.put(
        f"{BASE_URL}/service/rest/v1/security/users/admin/change-password",
        auth=("admin", initial_pwd),
        headers={"Content-Type": "text/plain"},
        data=config["NEXUS_PASSWORD"]
    )

    if response.status_code in [200, 204]:
        print("✅ Password changed successfully")
    else:
        raise Exception("❌ Failed to change Nexus password")


# -----------------------------
# CHECK REPO EXISTS
# -----------------------------
def repo_exists(repo_name):

    r = requests.get(
        f"{BASE_URL}/service/rest/v1/repositories",
        auth=(config["NEXUS_USER"], config["NEXUS_PASSWORD"])
    )

    repos = [repo["name"] for repo in r.json()]

    return repo_name in repos


# -----------------------------
# CREATE MAVEN HOSTED REPO
# -----------------------------
def create_maven_repo():

    repo_name = "maven-releases-custom"

    if repo_exists(repo_name):
        print("✅ Repository already exists. Skipping.")
        return repo_name

    print("\n📦 Creating Maven hosted repository...\n")

    data = {
        "name": repo_name,
        "online": True,
        "storage": {
            "blobStoreName": "default",
            "strictContentTypeValidation": True,
            "writePolicy": "ALLOW"
        },
        "maven": {
            "versionPolicy": "RELEASE",
            "layoutPolicy": "STRICT"
        }
    }

    response = requests.post(
        f"{BASE_URL}/service/rest/v1/repositories/maven/hosted",
        auth=(config["NEXUS_USER"], config["NEXUS_PASSWORD"]),
        json=data
    )

    if response.status_code in [200, 201]:
        print("✅ Repository created")
    else:
        raise Exception(f"❌ Repo creation failed: {response.text}")

    return repo_name


# -----------------------------
# GET REPO URL
# -----------------------------
def get_repo_url(repo_name):

    repo_url = f"{BASE_URL}/repository/{repo_name}/"

    print(f"✅ Repo URL: {repo_url}")

    # Save for later usage
    with open("nexus_repo_url.txt", "w") as f:
        f.write(repo_url)

    return repo_url


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def setup_nexus():

    print("\n🚀 NEXUS FULL CONFIGURATION STARTED\n")

    wait_for_nexus()

    initial_pwd = get_initial_password()

    if initial_pwd:
        change_password(initial_pwd)

    repo_name = create_maven_repo()

    repo_url = get_repo_url(repo_name)

    print("\n✅ Nexus FULLY CONFIGURED SUCCESSFULLY\n")

    return repo_url
