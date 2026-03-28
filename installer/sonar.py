import os
from utils.executor import run_command


# -----------------------------
# CHECK FUNCTIONS
# -----------------------------
def is_sonarqube_installed():
    return os.path.exists("/opt/sonarqube")


def is_sonarqube_running():
    return os.system("systemctl is-active --quiet sonarqube") == 0


def is_service_created():
    return os.path.exists("/etc/systemd/system/sonarqube.service")


# -----------------------------
# INSTALL SONARQUBE
# -----------------------------
def install_sonarqube():
    print("\n📊 Installing SonarQube ...\n")

    # -----------------------------
    # 1. System Config (REQUIRED)
    # -----------------------------
    run_command("sudo sysctl -w vm.max_map_count=262144")
    run_command("sudo sysctl -w fs.file-max=65536")

    # -----------------------------
    # 2. Install SonarQube
    # -----------------------------
    if is_sonarqube_installed():
        print("✅ SonarQube already installed. Skipping download.")
    else:
        print("⬇️ Downloading SonarQube...")

        run_command("""
        wget https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-9.9.3.79811.zip -O sonarqube.zip
        """)

        run_command("sudo apt-get install -y unzip")
        run_command("unzip sonarqube.zip")

        run_command("sudo mv sonarqube-* /opt/sonarqube")

        # Create sonar user
        run_command("sudo useradd sonar || true")

        # Permissions
        run_command("sudo chown -R sonar:sonar /opt/sonarqube")

    # -----------------------------
    # 3. Configure SonarQube
    # -----------------------------
    run_command("""
    sudo sed -i 's/#RUN_AS_USER=/RUN_AS_USER=sonar/' /opt/sonarqube/bin/linux-x86-64/sonar.sh
    """)

    # -----------------------------
    # 4. Create Systemd Service
    # -----------------------------
    if not is_service_created():
        print("⚙️ Creating SonarQube service...")

        run_command("""
        echo '[Unit]
Description=SonarQube service
After=syslog.target network.target

[Service]
Type=forking

ExecStart=/opt/sonarqube/bin/linux-x86-64/sonar.sh start
ExecStop=/opt/sonarqube/bin/linux-x86-64/sonar.sh stop

User=sonar
Group=sonar
Restart=always
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target' | sudo tee /etc/systemd/system/sonarqube.service
        """)

        run_command("sudo systemctl daemon-reload")
    else:
        print("✅ SonarQube service already exists.")

    # -----------------------------
    # 5. Start SonarQube
    # -----------------------------
    if not is_sonarqube_running():
        print("🚀 Starting SonarQube...")
        run_command("sudo systemctl enable sonarqube")
        run_command("sudo systemctl start sonarqube")
    else:
        print("✅ SonarQube already running.")

    print("\n⏳ SonarQube is starting (~1-2 minutes)...\n")

    run_command("sudo systemctl status sonarqube --no-pager")

    print("\n✅ SonarQube Setup Completed!\n")
