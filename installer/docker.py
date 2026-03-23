import os
from utils.executor import run_command


# -----------------------------
# CHECK FUNCTIONS
# -----------------------------
def is_docker_installed():
    return os.system("docker --version > /dev/null 2>&1") == 0


def is_docker_running():
    return os.system("systemctl is-active --quiet docker") == 0


def is_user_in_docker_group():
    return os.system("groups $USER | grep docker > /dev/null 2>&1") == 0


# -----------------------------
# INSTALL DOCKER
# -----------------------------
def install_docker():
    print("\n🐳 Installing Docker...\n")

    if is_docker_installed():
        print("✅ Docker already installed. Skipping installation.")
    else:
        run_command("sudo apt-get update")
        run_command("sudo apt-get install -y docker.io")

    if not is_docker_running():
        run_command("sudo systemctl start docker")
        run_command("sudo systemctl enable docker")
    else:
        print("✅ Docker service already running.")

    if not is_user_in_docker_group():
        run_command("sudo usermod -aG docker $USER")
        print("⚠️ Added user to docker group. Please logout/login once.")
    else:
        print("✅ User already in docker group.")


# -----------------------------
# FIX DOCKER CGROUP (SAFE)
# -----------------------------
def fix_docker():
    print("\n⚙️ Configuring Docker cgroup...\n")

    # Check if config already exists
    if os.path.exists("/etc/docker/daemon.json"):
        print("✅ Docker daemon.json already exists. Skipping config.")
    else:
        run_command("""
        sudo mkdir -p /etc/docker
        echo '{
          "exec-opts": ["native.cgroupdriver=systemd"]
        }' | sudo tee /etc/docker/daemon.json
        """)

        run_command("sudo systemctl restart docker")
        print("✅ Docker cgroup configured.")
