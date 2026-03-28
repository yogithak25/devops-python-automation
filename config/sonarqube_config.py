import os
import time
import requests
from config.env_loader import get_env

config = get_env()
BASE_URL = config["SONAR_URL"]


# -----------------------------
# ENV UPDATE FUNCTION
# -----------------------------
def update_env_with_sonar_token(token):

    print("\n🔐 Updating env.txt with SONAR_TOKEN...\n")

    env_file = "env.txt"

    if not token:
        print("❌ Token empty. Skipping...")
        return

    # Create env.txt if not exists
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write(f"SONAR_TOKEN={token}\n")
        print("✅ env.txt created with SONAR_TOKEN")
        return

    # Read file
    with open(env_file, "r") as f:
        lines = f.readlines()

    updated = False
    found = False

    for i, line in enumerate(lines):
        if line.startswith("SONAR_TOKEN="):
            found = True
            if line.strip() != f"SONAR_TOKEN={token}":
                lines[i] = f"SONAR_TOKEN={token}\n"
                updated = True

    if not found:
        lines.append(f"\nSONAR_TOKEN={token}\n")
        updated = True

    if updated:
        with open(env_file, "w") as f:
            f.writelines(lines)
        print("✅ SONAR_TOKEN updated in env.txt")
    else:
        print("✅ SONAR_TOKEN already up-to-date")


# -----------------------------
# AUTH HANDLER
# -----------------------------
def get_auth():
    try:
        r = requests.get(
            f"{BASE_URL}/api/system/status",
            auth=(config["SONAR_USER"], config["SONAR_NEW_PASSWORD"])
        )
        if r.status_code == 200:
            return (config["SONAR_USER"], config["SONAR_NEW_PASSWORD"])
    except:
        pass

    return (config["SONAR_USER"], config["SONAR_PASSWORD"])


# -----------------------------
# WAIT FOR SONAR
# -----------------------------
def wait_for_sonar():

    print("\n⏳ Waiting for SonarQube...\n")

    for i in range(30):
        try:
            r = requests.get(BASE_URL)
            if r.status_code == 200:
                print("✅ SonarQube Ready")
                return
        except:
            pass

        print(f"Waiting... ({i+1}/30)")
        time.sleep(10)

    raise Exception("❌ SonarQube not reachable")


# -----------------------------
# CHANGE PASSWORD
# -----------------------------
def change_password():

    print("\n🔐 Checking/Changing password...\n")

    response = requests.post(
        f"{BASE_URL}/api/users/change_password",
        auth=(config["SONAR_USER"], config["SONAR_PASSWORD"]),
        data={
            "login": config["SONAR_USER"],
            "previousPassword": config["SONAR_PASSWORD"],
            "password": config["SONAR_NEW_PASSWORD"]
        }
    )

    if response.status_code in [200, 204]:
        print("✅ Password updated")
    else:
        print("ℹ️ Password already changed")


# -----------------------------
# VALIDATE TOKEN
# -----------------------------
def is_token_valid(token):
    try:
        r = requests.get(
            f"{BASE_URL}/api/authentication/validate",
            auth=(token, "")
        )
        return r.status_code == 200 and r.json().get("valid")
    except:
        return False


# -----------------------------
# GENERATE TOKEN
# -----------------------------
def generate_token():

    existing_token = config.get("SONAR_TOKEN")

    # -----------------------------
    # 1. If env.txt token is valid → use it
    # -----------------------------
    if existing_token and is_token_valid(existing_token):
        print("✅ SONAR_TOKEN already valid in env.txt")
        return existing_token

    # -----------------------------
    # 2. If sonar_token.txt exists → reuse it
    # -----------------------------
    if os.path.exists("sonar_token.txt"):
        print("📄 Reading token from sonar_token.txt...")

        with open("sonar_token.txt", "r") as f:
            token = f.read().strip()

        if is_token_valid(token):
            print("✅ Token from file is valid")

            update_env_with_sonar_token(token)
            return token
        else:
            print("⚠️ Token in file invalid. Regenerating...")

    # -----------------------------
    # 3. Generate NEW token (only if needed)
    # -----------------------------
    print("\n🔑 Generating new Sonar token...\n")

    response = requests.post(
        f"{BASE_URL}/api/user_tokens/generate",
        auth=get_auth(),
        data={"name": f"jenkins-token-{int(time.time())}"}
    )

    if response.status_code == 200:
        token = response.json()["token"]

        print("✅ New token generated")

        # Save to file
        with open("sonar_token.txt", "w") as f:
            f.write(token)

        # Update env
        update_env_with_sonar_token(token)

        return token

    else:
        print("❌ Sonar API Error:", response.text)
        raise Exception("❌ Token generation failed")


# -----------------------------
# CREATE PROJECT
# -----------------------------
def create_project(project_key, project_name):

    response = requests.post(
        f"{BASE_URL}/api/projects/create",
        auth=get_auth(),
        data={
            "project": project_key,
            "name": project_name
        }
    )

    if response.status_code == 200:
        print(f"✅ {project_name} created")
    else:
        print(f"ℹ️ {project_name} already exists")


# -----------------------------
# QUALITY GATE
# -----------------------------
def create_quality_gate():

    gate_name = "custom-quality-gate"

    print("\n📊 Configuring Quality Gate...\n")

    response = requests.get(
        f"{BASE_URL}/api/qualitygates/show?name={gate_name}",
        auth=get_auth()
    )

    if response.status_code != 200:
        requests.post(
            f"{BASE_URL}/api/qualitygates/create",
            auth=get_auth(),
            data={"name": gate_name}
        )
        print("✅ Quality gate created")
    else:
        print("✅ Quality gate already exists")

    # Always ensure condition
    requests.post(
        f"{BASE_URL}/api/qualitygates/create_condition",
        auth=get_auth(),
        data={
            "gateName": gate_name,
            "metric": "coverage",
            "op": "LT",
            "error": "20"
        }
    )

    print("✅ Coverage condition set (>=20%)")

    return gate_name


# -----------------------------
# SET DEFAULT QUALITY GATE
# -----------------------------
def set_default_quality_gate(gate_name):

    requests.post(
        f"{BASE_URL}/api/qualitygates/set_as_default",
        auth=get_auth(),
        data={"name": gate_name}
    )

    print("✅ Set as default quality gate")


# -----------------------------
# ASSIGN QUALITY GATE
# -----------------------------
def assign_quality_gate(project_key, gate_name):

    requests.post(
        f"{BASE_URL}/api/qualitygates/select",
        auth=get_auth(),
        data={
            "projectKey": project_key,
            "gateName": gate_name
        }
    )

    print(f"✅ {project_key} linked to quality gate")


# -----------------------------
# WEBHOOK
# -----------------------------
def add_webhook():

    print("\n🔗 Adding Jenkins webhook...\n")

    response = requests.get(
        f"{BASE_URL}/api/webhooks/list",
        auth=get_auth()
    )

    existing = response.json().get("webhooks", [])

    for w in existing:
        if "jenkins" in w["name"]:
            print("✅ Webhook already exists")
            return

    requests.post(
        f"{BASE_URL}/api/webhooks/create",
        auth=get_auth(),
        data={
            "name": "jenkins-webhook",
            "url": f"{config['JENKINS_URL']}/sonarqube-webhook/"
        }
    )

    print("✅ Webhook created")


# -----------------------------
# MAIN
# -----------------------------
def setup_sonarqube():

    print("\n🚀 SONARQUBE FULL CONFIGURATION STARTED\n")

    wait_for_sonar()
    change_password()

    token = generate_token()

    create_project("java-devops-project", "java-devops-project")
    create_project("python-devops-project", "python-devops-project")

    gate = create_quality_gate()
    set_default_quality_gate(gate)

    assign_quality_gate("java-devops-project", gate)
    assign_quality_gate("python-devops-project", gate)

    add_webhook()

    print("\n✅ SONARQUBE FULLY CONFIGURED SUCCESSFULLY\n")

    return token
