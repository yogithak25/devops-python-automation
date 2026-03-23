import os
from utils.executor import run_command


# -----------------------------
# CHECK FUNCTIONS
# -----------------------------
def is_maven_installed():
    return os.system("mvn -version > /dev/null 2>&1") == 0


def is_java_installed():
    return os.system("java -version > /dev/null 2>&1") == 0


# -----------------------------
# INSTALL MAVEN
# -----------------------------
def install_maven():

    print("\n📦 Installing Maven...\n")

    # -----------------------------
    # 1. Java Check (required)
    # -----------------------------
    if not is_java_installed():
        print("Installing Java (required for Maven)...")
        run_command("sudo apt-get update")
        run_command("sudo apt-get install -y openjdk-17-jdk")
    else:
        print("✅ Java already installed.")

    # -----------------------------
    # 2. Install Maven
    # -----------------------------
    if not is_maven_installed():
        print("⬇️ Installing Maven...")
        run_command("sudo apt-get update")
        run_command("sudo apt-get install -y maven")
    else:
        print("✅ Maven already installed.")

    # -----------------------------
    # 3. Verify Installation
    # -----------------------------
    run_command("mvn -version")

    print("\n✅ Maven Setup Completed Successfully!\n")
