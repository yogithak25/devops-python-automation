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


def is_bootstrap_done():
    return os.path.exists("/var/lib/jenkins/jenkins_token.txt")


# -----------------------------
# UPDATE env.txt WITH TOKEN
# -----------------------------
def update_env_with_jenkins_token():

    print("\n🔐 Updating env.txt with Jenkins Token...\n")

    token_file = "/var/lib/jenkins/jenkins_token.txt"
    env_file = "env.txt"

    if not os.path.exists(token_file):
        print("❌ Token file not found. Skipping...")
        return

    token = os.popen(f"sudo cat {token_file}").read().strip()

    if not token:
        print("❌ Token empty. Skipping...")
        return

    # Create env.txt if not exists
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write(f"JENKINS_TOKEN={token}\n")
        print("✅ env.txt created with Jenkins token")
        return

    # Read existing env
    with open(env_file, "r") as f:
        lines = f.readlines()

    updated = False
    found = False

    for i, line in enumerate(lines):
        if line.startswith("JENKINS_TOKEN="):
            found = True
            if line.strip() != f"JENKINS_TOKEN={token}":
                lines[i] = f"JENKINS_TOKEN={token}\n"
                updated = True

    if not found:
        lines.append(f"\nJENKINS_TOKEN={token}\n")
        updated = True

    if updated:
        with open(env_file, "w") as f:
            f.writelines(lines)
        print("✅ Jenkins token updated in env.txt")
    else:
        print("✅ Jenkins token already up-to-date")


# -----------------------------
# INSTALL JENKINS
# -----------------------------
def install_jenkins():

    print("\n⚙️ Installing Jenkins...\n")

    # -----------------------------
    # 1. Java
    # -----------------------------
    if not is_java_installed():
        run_command("sudo apt-get update")
        run_command("sudo apt-get install -y openjdk-17-jdk")
    else:
        print("✅ Java already installed.")

    # -----------------------------
    # 2. Repo
    # -----------------------------
    if not is_repo_added():
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
        print("✅ Repo already added.")

    # -----------------------------
    # 3. Install Jenkins
    # -----------------------------
    if not is_jenkins_installed():
        run_command("sudo apt-get install -y jenkins")
    else:
        print("✅ Jenkins already installed.")

    # -----------------------------
    # 4. Disable setup wizard
    # -----------------------------
    if not is_bootstrap_done():
        print("🔧 Disabling setup wizard...")

        run_command("""
        sudo sed -i 's|^JAVA_ARGS=.*|JAVA_ARGS="-Djenkins.install.runSetupWizard=false"|' /etc/default/jenkins || \
        echo 'JAVA_ARGS="-Djenkins.install.runSetupWizard=false"' | sudo tee -a /etc/default/jenkins
        """)
    else:
        print("✅ Setup wizard already disabled.")

    # -----------------------------
    # 5. Bootstrap (USER + TOKEN)
    # -----------------------------
    if not is_bootstrap_done():
        print("🔧 Creating admin user + token...")

        run_command("sudo mkdir -p /var/lib/jenkins/init.groovy.d")

        run_command("""
        sudo tee /var/lib/jenkins/init.groovy.d/bootstrap.groovy > /dev/null <<EOF
#!groovy
import jenkins.model.*
import hudson.security.*
import jenkins.security.*

def instance = Jenkins.getInstance()

def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("admin", "jenkins")
instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

instance.save()

def user = hudson.model.User.get("admin")
def token = user.getProperty(ApiTokenProperty.class).tokenStore.generateNewToken("automation-token")

def tokenValue = token.plainValue

new File("/var/lib/jenkins/jenkins_token.txt").text = tokenValue
EOF
        """)
    else:
        print("✅ Bootstrap already done.")

    # -----------------------------
    # 6. Start Jenkins
    # -----------------------------
    if not is_jenkins_running():
        run_command("sudo systemctl enable jenkins")
        run_command("sudo systemctl start jenkins")
    else:
        print("✅ Jenkins already running.")

    # -----------------------------
    # 7. Docker permission
    # -----------------------------
    run_command("sudo usermod -aG docker jenkins")

    # Restart ONLY first time
    if not is_bootstrap_done():
        print("🔄 Restarting Jenkins...")
        run_command("sudo systemctl restart jenkins")
        run_command("sleep 60")

    # -----------------------------
    # 8. UPDATE ENV FILE
    # -----------------------------
    update_env_with_jenkins_token()

    print("\n✅ Jenkins Fully Automated Setup Completed!\n")
