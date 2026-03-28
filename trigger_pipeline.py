import requests
from config.env_loader import get_env

config = get_env()


def trigger_pipeline(job_name):
    url = f"{config['JENKINS_URL']}/job/{job_name}/build"

    print(f"\n🚀 Triggering {job_name}...\n")

    response = requests.post(
        url,
        auth=(config["JENKINS_USER"], config["JENKINS_TOKEN"])
    )

    if response.status_code in [200, 201]:
        print(f"✅ {job_name} triggered successfully!\n")
    else:
        print(f"❌ Failed to trigger {job_name}")
        print("Response:", response.text)


def main():

    print("\n🎯 PIPELINE TRIGGER MENU\n")
    print("1️⃣  Java Pipeline")
    print("2️⃣  Python Pipeline\n")

    user_input = input("👉 Enter your choice (java/python): ").strip().lower()

    if user_input == "java":
        trigger_pipeline("java-devops-pipeline")

    elif user_input == "python":
        trigger_pipeline("python-devops-pipeline")

    else:
        print("\n❌ Invalid input!")
        print("👉 Please enter ONLY: java OR python\n")


if __name__ == "__main__":
    main()
