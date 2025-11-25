import paramiko
import time

def debug_server():
    hostname = "116.203.232.88"
    username = "cognee"
    password = "Cognee2025"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected!")
        venv_python = "/opt/cognee/.venv/bin/python"
        # 1. Check logs
        print("--- Checking Logs ---")
        stdin, stdout, stderr = client.exec_command(f"echo {password} | sudo -S journalctl -u cognee-api -n 20 --no-pager")
        print(stdout.read().decode().strip())

        # 2. Upload script via SFTP
        print("\n--- Uploading Forgery Script ---")
        sftp = client.open_sftp()
        script_content = """
import sqlite3
import jwt
import datetime
import uuid
import sys

db_path = '/opt/cognee_system/databases/cognee_db'
email = 'gearcrew_test@example.com'
secret = 'super_secret'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Tables ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(tables)
    
    user_table = 'user'
    if not any('user' in t[0] for t in tables):
        if any('users' in t[0] for t in tables):
            user_table = 'users'
    
    print(f"Using table: {user_table}")
    
    cursor.execute(f"SELECT id FROM {user_table} WHERE email=?", (email,))
    row = cursor.fetchone()
    if row:
        user_id = row[0]
        print(f'User ID: {user_id}')
        payload = {
            'sub': str(user_id),
            'aud': ['fastapi-users:auth'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }
        token = jwt.encode(payload, secret, algorithm='HS256')
        print(f'FORGED_TOKEN: {token}')
    else:
        print(f'User {email} not found in DB')
    conn.close()
except Exception as e:
    print(f'Error: {e}')
"""
        with sftp.file('/tmp/forge_token.py', 'w') as f:
            f.write(script_content)
        sftp.close()
        print("Script uploaded.")

        # 3. Run the script
        print("\n--- Running Forgery Script ---")
        venv_python = "/opt/cognee/.venv/bin/python"
        stdin, stdout, stderr = client.exec_command(f"{venv_python} /tmp/forge_token.py")
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out: print(f"STDOUT:\n{out}")
        if err: print(f"STDERR:\n{err}")

                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_server()
