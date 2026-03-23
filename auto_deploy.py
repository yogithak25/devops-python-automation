import requests
import os
from requests.auth import HTTPBasicAuth


def load_env(file_path="env.txt"):
    """Load environment variables from env.txt"""
    with open(file_path) as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value


# Load env variables
load_env()

JENKINS_URL = os.getenv("JENKINS_URL")
USERNAME = os.getenv("JENKINS_USER")
API_TOKEN = os.getenv("JENKINS_API_TOKEN")

JAVA_JOB = os.getenv("JAVA_JOB")
PYTHON_JOB = os.getenv("PYTHON_JOB")


def trigger_pipeline(job_name):

    url = f"{JENKINS_URL}/job/{job_name}/build"

    response = requests.post(
        url,
        auth=HTTPBasicAuth(USERNAME, API_TOKEN)
    )

    if response.status_code in [200, 201]:
        print(f"Pipeline '{job_name}' triggered successfully")
    else:
        print("Failed to trigger pipeline")
        print(response.text)


def main():

    app_type = input("Enter application type (java/python): ").lower()

    if app_type == "java":
        trigger_pipeline(JAVA_JOB)

    elif app_type == "python":
        trigger_pipeline(PYTHON_JOB)

    else:
        print("Invalid input. Choose 'java' or 'python'")


if __name__ == "__main__":
    main()

