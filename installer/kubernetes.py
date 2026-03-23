import os
from utils.executor import run_command


# -----------------------------
# CHECK FUNCTIONS
# -----------------------------
def is_k8s_initialized():
    return os.path.exists("/etc/kubernetes/admin.conf")


def is_containerd_installed():
    return os.system("containerd --version > /dev/null 2>&1") == 0


def is_k8s_installed():
    return os.system("kubectl version --client > /dev/null 2>&1") == 0


def is_cluster_running():
    return os.system("kubectl get nodes > /dev/null 2>&1") == 0


# -----------------------------
# 1. ENVIRONMENT SETUP
# -----------------------------
def prepare_environment():
    print("\n🔧 Preparing Kubernetes Environment...\n")

    run_command("sudo swapoff -a")
    run_command("sudo sed -i '/ swap / s/^/#/' /etc/fstab")

    run_command("sudo modprobe overlay || true")
    run_command("sudo modprobe br_netfilter || true")

    run_command("""
    echo -e "overlay\nbr_netfilter" | sudo tee /etc/modules-load.d/k8s.conf
    """)

    run_command("""
    echo -e "net.bridge.bridge-nf-call-iptables=1\nnet.bridge.bridge-nf-call-ip6tables=1\nnet.ipv4.ip_forward=1" \
    | sudo tee /etc/sysctl.d/k8s.conf
    """)

    run_command("sudo sysctl --system")


# -----------------------------
# 2. INSTALL CONTAINERD
# -----------------------------
def install_containerd():
    print("\n📦 Installing Containerd...\n")

    if is_containerd_installed():
        print("✅ containerd already installed.")
        return

    run_command("sudo apt-get update")
    run_command("sudo apt-get install -y containerd")

    run_command("sudo mkdir -p /etc/containerd")

    run_command("""
    containerd config default | sudo tee /etc/containerd/config.toml
    """)

    run_command("""
    sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
    """)

    run_command("sudo systemctl restart containerd")
    run_command("sudo systemctl enable containerd")


# -----------------------------
# 3. INSTALL KUBERNETES
# -----------------------------
def install_kubernetes_packages():
    print("\n📦 Installing Kubernetes Components...\n")

    if is_k8s_installed():
        print("✅ Kubernetes already installed.")
        return

    run_command("sudo apt-get update")
    run_command("sudo apt-get install -y apt-transport-https ca-certificates curl gnupg")

    run_command("sudo mkdir -p /etc/apt/keyrings")

    run_command("""
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key \
    | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    """)

    run_command("""
    echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \
    https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /" \
    | sudo tee /etc/apt/sources.list.d/kubernetes.list
    """)

    run_command("sudo apt-get update")
    run_command("sudo apt-get install -y kubelet kubeadm kubectl")
    run_command("sudo apt-mark hold kubelet kubeadm kubectl")


# -----------------------------
# 4. INIT CLUSTER
# -----------------------------
def initialize_cluster():
    print("\n🚀 Initializing Kubernetes Cluster...\n")

    if is_k8s_initialized():
        print("✅ Kubernetes already initialized. Skipping kubeadm init.")
        return

    run_command("""
    sudo kubeadm init \
    --pod-network-cidr=10.244.0.0/16 \
    --cri-socket=unix:///run/containerd/containerd.sock
    """)


# -----------------------------
# 5. CONFIGURE KUBECTL
# -----------------------------
def configure_kubectl():
    print("\n⚙️ Configuring kubectl...\n")

    if os.path.exists(os.path.expanduser("~/.kube/config")):
        print("✅ kubeconfig already exists.")
        return

    run_command("mkdir -p $HOME/.kube")
    run_command("sudo cp /etc/kubernetes/admin.conf $HOME/.kube/config")
    run_command("sudo chown $(id -u):$(id -g) $HOME/.kube/config")


# -----------------------------
# 6. WAIT FOR API SERVER
# -----------------------------
def wait_for_api_server():
    print("\n⏳ Waiting for API Server...\n")

    for i in range(20):
        if os.system("kubectl get nodes > /dev/null 2>&1") == 0:
            print("✅ API Server Ready")
            return
        print(f"Waiting... ({i+1}/20)")
        run_command("sleep 5")


# -----------------------------
# 7. INSTALL NETWORK
# -----------------------------
def install_network():
    print("\n🌐 Installing Flannel Network...\n")

    # Apply only once (safe anyway)
    run_command("""
    kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/v0.25.5/Documentation/kube-flannel.yml
    """)

    run_command("sudo systemctl restart containerd")
    run_command("sudo systemctl restart kubelet")

    run_command("sleep 60")


# -----------------------------
# 8. FINALIZE
# -----------------------------
def finalize_cluster():
    print("\n⏳ Stabilizing Cluster...\n")

    run_command("sleep 30")

    run_command("""
    kubectl taint nodes --all node-role.kubernetes.io/control-plane- || true
    """)

    run_command("kubectl get nodes")
    run_command("kubectl get pods -A")


# -----------------------------
# MAIN
# -----------------------------
def install_kubernetes():

    print("\n🔥 Kubernetes Setup (Idempotent)...\n")

    if is_cluster_running():
        print("✅ Kubernetes cluster already running. Skipping full setup.")
        run_command("kubectl get nodes")
        return

    prepare_environment()
    install_containerd()
    install_kubernetes_packages()
    initialize_cluster()
    configure_kubectl()
    wait_for_api_server()
    install_network()
    finalize_cluster()

    print("\n✅ Kubernetes Cluster Ready!\n")
