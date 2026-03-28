import os
from utils.executor import run_command


# -----------------------------
# CHECK FUNCTIONS
# -----------------------------
def is_java_installed():
    return os.system("java -version > /dev/null 2>&1") == 0


def is_nexus_installed():
    return os.path.exists("/opt/nexus")


def is_nexus_running():
    return os.system("systemctl is-active --quiet nexus") == 0


def is_nexus_service_created():
    return os.path.exists("/etc/systemd/system/nexus.service")


# -----------------------------
# INSTALL NEXUS
# -----------------------------
def install_nexus():
    print("\n📦 Installing Nexus ...\n")

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
    # 2. Nexus Installation
    # -----------------------------
    if is_nexus_installed():
        print("✅ Nexus already installed. Skipping download & extract.")
    else:
        print("⬇️ Downloading Nexus...")

        run_command("""
         wget https://download.sonatype.com/nexus/3/nexus-3.87.1-01-linux-x86_64.tar.gz -O nexus.tar.gz
        """)

        run_command("tar -xvf nexus.tar.gz")

        run_command("sudo mv nexus-* /opt/nexus")
        run_command("sudo mv sonatype-work /opt/")

        # Create nexus user
        run_command("sudo useradd nexus || true")

        # Set permissions
        run_command("sudo chown -R nexus:nexus /opt/nexus")
        run_command("sudo chown -R nexus:nexus /opt/sonatype-work")


    # -----------------------------
    # 3. Create Systemd Service
    # -----------------------------
    if not is_nexus_service_created():
        print("⚙️ Creating Nexus service...")

        run_command("""
        echo '[Unit]
Description=Nexus Repository Manager
After=network.target

[Service]
Type=forking
LimitNOFILE=65536
User=nexus
Group=nexus
ExecStart=/opt/nexus/bin/nexus start
ExecStop=/opt/nexus/bin/nexus stop
Restart=on-abort

[Install]
WantedBy=multi-user.target' | sudo tee /etc/systemd/system/nexus.service
        """)

        run_command("sudo systemctl daemon-reload")
    else:
        print("✅ Nexus service already exists.")

    # -----------------------------
    # 4. Start Nexus
    # -----------------------------
    if not is_nexus_running():
        print("🚀 Starting Nexus...")
        run_command("sudo systemctl enable nexus")
        run_command("sudo systemctl start nexus")
    else:
        print("✅ Nexus already running.")

    print("\n⏳ Nexus is starting... (takes ~1-2 minutes)\n")

    # -----------------------------
    # 5. Show Status
    # -----------------------------
    run_command("sudo systemctl status nexus --no-pager")

    print("\n✅ Nexus Setup Completed Successfully!\n")
