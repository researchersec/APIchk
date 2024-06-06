import requests
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import os


def load_config(config_file):
    with open(config_file, "r") as file:
        config = json.load(file)
    return config


def setup_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def get_api_key(env_var_name):
    if env_var_name:
        return os.getenv(env_var_name, "")
    return ""


def test_api_url(url, env_var_name, timeout, retries):
    api_key = get_api_key(env_var_name)
    if api_key and "api-key=" in url:
        url = f"{url}{api_key}"
    headers = (
        {"Authorization": f"Bearer {api_key}"}
        if api_key and "api-key=" not in url
        else {}
    )
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            status_code = response.status_code
            success = status_code == 200
            return {"url": url, "status_code": status_code, "success": success}
        except requests.exceptions.RequestException as e:
            attempt += 1
            if attempt >= retries:
                return {
                    "url": url,
                    "status_code": None,
                    "success": False,
                    "error": str(e),
                }


def print_results(results):
    for result in results:
        if result["success"]:
            print(
                f"URL: {result['url']} is reachable. Status code: {result['status_code']}"
            )
            logging.info(
                f"URL: {result['url']} is reachable. Status code: {result['status_code']}"
            )
        else:
            error_message = result.get("error", "Unknown error")
            print(
                f"URL: {result['url']} is not reachable. Status code: {result['status_code']}. Error: {error_message}"
            )
            logging.error(
                f"URL: {result['url']} is not reachable. Status code: {result['status_code']}. Error: {error_message}"
            )


def main():
    load_dotenv()  # Load environment variables from .env file
    config_file = "config.json"
    log_file = "api_test.log"

    config = load_config(config_file)
    api_urls = config["api_urls"]
    timeout = config["timeout"]
    retries = config["retry_attempts"]

    setup_logging(log_file)

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {
            executor.submit(test_api_url, url, env_var_name, timeout, retries): url
            for url, env_var_name in api_urls.items()
        }
        results = []
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)

    print_results(results)


if __name__ == "__main__":
    main()
