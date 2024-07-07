import boto3
import os
import json


def get_secret():
    secret_name = "journeymanai-api-secrets"
    region_name = "us-east-1"  # e.g., us-west-2

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    # Fetch the secret
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response["SecretString"]
    return json.loads(secret)


secrets = get_secret()

# Set the secrets as environment variables
for key, value in secrets.items():
    os.environ[key] = value
