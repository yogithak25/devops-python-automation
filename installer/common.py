from utils.executor import run_command

def update_system():
    run_command("sudo apt update -y && sudo apt upgrade -y")

def install_basic_tools():
    run_command("sudo apt install -y curl wget unzip apt-transport-https ca-certificates gnupg lsb-release software-properties-common")

