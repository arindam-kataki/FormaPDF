# test_env_loading.py
import os
print("=== BEFORE loading .env ===")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")

try:
    from dotenv import load_dotenv
    result = load_dotenv()
    print(f"load_dotenv() result: {result}")
except Exception as e:
    print(f"Error loading dotenv: {e}")

print("\n=== AFTER loading .env ===")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
print(f"DB_TYPE: {os.getenv('DB_TYPE')}")