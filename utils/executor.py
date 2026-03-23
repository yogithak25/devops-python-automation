import subprocess

def run_command(command):
    print(f"\n🚀 Executing: {command}\n")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ ERROR:", e.stderr)

