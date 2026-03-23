import os
from utils.executor import run_command


# -----------------------------
# CHECK FUNCTIONS
# -----------------------------
def is_python_installed():
    return os.system("python3 --version > /dev/null 2>&1") == 0


def is_venv_created():
    return os.path.exists("devops-env")


def is_requirements_installed():
    return os.path.exists("devops-env/lib")


# -----------------------------
# INSTALL PYTHON ENVIRONMENT
# -----------------------------
def install_python_env():

    print("\n🐍 Setting up Python Environment...\n")

    # -----------------------------
    # 1. Install Python & tools
    # -----------------------------
    if not is_python_installed():
        print("Installing Python...")
        run_command("sudo apt-get update")
        run_command("sudo apt-get install -y python3 python3-pip python3-venv")
    else:
        print("✅ Python already installed.")

    # -----------------------------
    # 2. Create Virtual Environment
    # -----------------------------
    if not is_venv_created():
        print("📦 Creating virtual environment...")
        run_command("python3 -m venv devops-env")
    else:
        print("✅ Virtual environment already exists.")

    # -----------------------------
    # 3. Install Requirements
    # -----------------------------
    if os.path.exists("requirements.txt"):
        print("📥 Installing Python dependencies...")

        run_command("""
        bash -c 'source devops-env/bin/activate && pip install -r requirements.txt'
        """)
    else:
        print("⚠️ requirements.txt not found. Skipping...")

    print("\n✅ Python Environment Ready!\n")
