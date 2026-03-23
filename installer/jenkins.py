import os
from utils.executor import run_command


# -----------------------------
# CHECK FUNCTIONS
# -----------------------------
def is_java_installed():
    return os.system("java -version > /dev/null 2>&1") == 0


def is_jenkins_installed():
    return os.system("dpkg -l | grep jenkins > /dev/null 2>&1") == 0


def is_jenkins_running():
    return os.system("systemctl is-active --quiet jenkins") == 0


def is_repo_added():
    return os.path.exists("/etc/apt/sources.list.d/jenkins.list")


# -----------------------------
# INSTALL JENKINS
# -----------------------------
def install_jenkins():

    print("\n⚙️ Installing Jenkins...\n")

    # -----------------------------
    # 1. Java Check
    # -----------------------------
    if not is_java_installed():
        print("Installing Java...")
        run_command("sudo apt-get update")
        run_command("sudo apt-get install -y openjdk-17-jdk")
    else:
        print("✅ Java already installed. Skipping...")

    # -----------------------------
    # 2. Add Jenkins Repo (only once)
    # -----------------------------
    if not is_repo_added():
        print("➕ Adding Jenkins repository...")

        run_command("sudo mkdir -p /etc/apt/keyrings")

        run_command("""
        sudo wget -O /etc/apt/keyrings/jenkins-keyring.asc \
        https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key
        """)

        run_command("""
        echo "deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] \
        https://pkg.jenkins.io/debian-stable binary/" \
        | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
        """)

        run_command("sudo apt-get update")
    else:
        print("✅ Jenkins repository already added.")

    # -----------------------------
    # 3. Install Jenkins
    # -----------------------------
    if not is_jenkins_installed():
        print("📦 Installing Jenkins...")
        run_command("sudo apt-get install -y jenkins")
    else:
        print("✅ Jenkins already installed.")

    # -----------------------------
    # 4. Start Jenkins
    # -----------------------------
    if not is_jenkins_running():
        print("🚀 Starting Jenkins...")
        run_command("sudo systemctl enable jenkins")
        run_command("sudo systemctl start jenkins")
        #Add Jenkins to Docker group
        run_command("sudo usermod -aG docker jenkins")
        run_command("sudo systemctl restart jenkins")
    else:
        print("✅ Jenkins already running.")

    print("\n✅ Jenkins Setup Completed Successfully!\n")
