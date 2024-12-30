import argparse
import json
from typing import Optional

import boto3

EnvVarDataType = dict[str, Optional[str]]


def find_env_var_name_and_value(line: str) -> tuple[Optional[str], Optional[str]]:
    line = line.strip()
    if not line:
        return None, None
    if line.startswith("#"):
        return None, None
    if "=" not in line:
        return None, None

    line = line.replace("export ", "")
    name, value = line.split("=", 1)
    return name, value


def read_file(path_to_env_file: str) -> EnvVarDataType:
    env_vars: EnvVarDataType = {}
    with open(path_to_env_file) as f:
        lines = f.readlines()
        for line in lines:
            name, value = find_env_var_name_and_value(line)
            if name:  # We only look for a name here since value may be None (e.g. DB_PASSWORD=)
                env_vars[name] = value
    return env_vars


def read_secrets(secrets_manager_id: str) -> EnvVarDataType:
    env_vars: EnvVarDataType = {}
    client = boto3.client("secretsmanager")
    raw_secret = client.get_secret_value(
        SecretId=secrets_manager_id,
    ).get("SecretString", "{}")
    env_vars = json.loads(raw_secret)
    return env_vars


def print_diff(local_env_vars: EnvVarDataType, secret_env_vars: EnvVarDataType):
    for key, value in local_env_vars.items():
        if key in secret_env_vars:
            if value != secret_env_vars[key]:
                print(f"{key} is different")
        else:
            print(f"{key} is missing in secrets")

    print()

    for key, value in secret_env_vars.items():
        if key not in local_env_vars:
            print(f"{key} is missing in local")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--env-file-path", type=str, required=True)
    parser.add_argument("-s", "--secrets-manager-id", type=str, required=True)
    args = parser.parse_args()

    local_env_vars = read_file(args.env_file_path)
    secret_env_vars = read_secrets(args.secrets_manager_id)

    print_diff(local_env_vars, secret_env_vars)


if __name__ == "__main__":
    main()
