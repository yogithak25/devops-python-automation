import os
from utils.executor import run_command


# -----------------------------
# CHECK: ArgoCD Installed
# -----------------------------
def is_argocd_installed():
    output = os.popen(
        "kubectl get pods -n argocd --no-headers 2>/dev/null"
    ).read()

    return "argocd-server" in output


# -----------------------------
# CHECK: Service Type
# -----------------------------
def is_nodeport():
    output = os.popen(
        "kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.type}' 2>/dev/null"
    ).read().strip()

    return output == "NodePort"


# -----------------------------
# WAIT FOR ARGOCD PODS
# -----------------------------
def wait_for_argocd():
    print("\n⏳ Waiting for ArgoCD pods...\n")

    for i in range(30):
        output = os.popen("kubectl get pods -n argocd").read()

        if "argocd-server" in output and "Running" in output:
            print("✅ ArgoCD pods are running!")
            return

        print(f"Waiting... ({i+1}/30)")
        run_command("sleep 10")

    print("❌ ArgoCD pods not ready!")


# -----------------------------
# EXPOSE SERVICE
# -----------------------------
def expose_argocd():
    print("\n🌐 Checking ArgoCD Service Type...\n")

    if is_nodeport():
        print("✅ ArgoCD already exposed via NodePort. Skipping...")
        return

    print("🔧 Converting ArgoCD service to NodePort...")

    run_command("""
    kubectl patch svc argocd-server -n argocd \
    -p '{"spec": {"type": "NodePort"}}'
    """)

    print("✅ ArgoCD exposed via NodePort!")


# -----------------------------
# INSTALL ARGOCD
# -----------------------------
def install_argocd():

    print("\n🚀 Installing ArgoCD...\n")

    # Ensure namespace exists
    run_command("kubectl get ns argocd || kubectl create ns argocd")

    # Install if not exists
    if not is_argocd_installed():

        print("📦 Applying ArgoCD manifests...")

        run_command("""
        kubectl apply -n argocd \
        -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml --server-side
        """)

        wait_for_argocd()

    else:
        print("✅ ArgoCD already installed.")

    # Expose service
    expose_argocd()

    # Show service details
    print("\n🔎 ArgoCD Service Info:\n")
    run_command("kubectl get svc argocd-server -n argocd")

    print("\n✅ ArgoCD Setup Completed!\n")
