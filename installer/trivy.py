import os
from utils.executor import run_command


# -----------------------------
# CHECK FUNCTIONS
# -----------------------------
def is_trivy_installed():
    return os.system("trivy --version > /dev/null 2>&1") == 0


def is_trivy_repo_added():
    return os.path.exists("/etc/apt/sources.list.d/trivy.list")


def is_trivy_key_added():
    return os.path.exists("/etc/apt/keyrings/trivy.gpg")


# -----------------------------
# INSTALL TRIVY
# -----------------------------
def install_trivy():

    print("\n🔐 Installing Trivy...\n")

    # -----------------------------
    # 1. Install base packages (safe)
    # -----------------------------
    run_command("sudo apt-get update")
    run_command("sudo apt-get install -y wget gnupg lsb-release")

    # -----------------------------
    # 2. Add keyrings directory
    # -----------------------------
    run_command("sudo mkdir -p /etc/apt/keyrings")

    # -----------------------------
    # 3. Add GPG Key (only once)
    # -----------------------------
    if not is_trivy_key_added():
        print("🔑 Adding Trivy GPG key...")
        run_command(
            "wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key "
            "| sudo gpg --dearmor -o /etc/apt/keyrings/trivy.gpg"
        )
    else:
        print("✅ Trivy GPG key already exists.")

    # -----------------------------
    # 4. Add Repository (only once)
    # -----------------------------
    if not is_trivy_repo_added():
        print("➕ Adding Trivy repository...")
        run_command(
            'echo "deb [signed-by=/etc/apt/keyrings/trivy.gpg] '
            'https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" '
            '| sudo tee /etc/apt/sources.list.d/trivy.list'
        )
        run_command("sudo apt-get update")
    else:
        print("✅ Trivy repository already exists.")

    # -----------------------------
    # 5. Install Trivy
    # -----------------------------
    if not is_trivy_installed():
        print("📦 Installing Trivy...")
        run_command("sudo apt-get install -y trivy")
    else:
        print("✅ Trivy already installed.")

    # -----------------------------
    # 6. Verify
    # -----------------------------
    run_command("trivy --version")

    print("\n✅ Trivy Setup Completed Successfully!\n")
