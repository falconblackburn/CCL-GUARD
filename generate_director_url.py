import subprocess
import re
import time
import os
import sys

def update_env(key, value):
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write(f"{key}={value}\n")
        return

    with open(env_file, "r") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key}={value}\n")

    with open(env_file, "w") as f:
        f.writelines(new_lines)

def generate_tunnel():
    print("[*] Starting Cloudflare Tunnel for Director Dashboard (Port 5005)...")
    
    # Run cloudflared tunnel --url http://localhost:5005
    # We use stderr because cloudflared logs its URL to stderr
    process = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:5005"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    public_url = None
    pattern = r"https://[a-zA-Z0-9-]+\.trycloudflare\.com"

    start_time = time.time()
    timeout = 30 # 30 seconds timeout

    print("[*] Extracting public URL...")
    try:
        while time.time() - start_time < timeout:
            line = process.stderr.readline()
            if not line:
                break
            
            # Look for the URL in the logs
            match = re.search(pattern, line)
            if match:
                public_url = match.group(0)
                break
            
            # Print important logs
            if "error" in line.lower():
                print(f"[ERROR] {line.strip()}")
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
    finally:
        if not public_url:
            print("[!] Failed to extract Cloudflare URL. Ensure cloudflared is installed and Port 5005 is available.")
            process.terminate()
            return None

    print(f"[SUCCESS] Director Public URL: {public_url}")
    
    # Update .env
    update_env("DIRECTOR_PUBLIC_URL", f'"{public_url}"')
    update_env("PARENT_SERVER_URL", f'"{public_url}"')
    
    print("[*] .env file updated with PARENT_SERVER_URL.")
    
    # We keep the process running in the background if we want it to stay alive, 
    # but for this script, we'll just return the URL and let the user know they need it running.
    # Actually, in a production scenario, they'd use a named tunnel.
    # For this 'quick' request, we'll keep it running until the script ends.
    return public_url, process

if __name__ == "__main__":
    url, proc = generate_tunnel()
    if url:
        print(f"\n--- MISSION ACCOMPLISHED ---")
        print(f"Your Director Server is now live at: {url}")
        print(f"Keep this script running to maintain the tunnel, or set up a persistent tunnel.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Shutting down tunnel...")
            proc.terminate()
