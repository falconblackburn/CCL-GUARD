from flask import Flask, request, jsonify, render_template
from parent_database import init_parent_db, register_or_update_client, get_all_clients, delete_client, toggle_client_status
import datetime
import threading
import sqlite3
import requests
import os
import zipfile
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = "director-functional-fallback-key"
init_parent_db()

@app.route("/")
def dashboard():
    clients = get_all_clients()
    
    # Simple logic to mark clients as offline if last_seen > 3 minutes ago
    processed_clients = []
    total_incidents = 0
    online_count = 0
    
    for row in clients:
        c_id, name, url, status, last_seen, incidents = row
        total_incidents += incidents
        
        # Parse last seen
        last_seen_dt = datetime.datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S")
        if (datetime.datetime.now() - last_seen_dt).total_seconds() > 180:
            status = 'Offline'
        else:
            online_count += 1
            
        processed_clients.append({
            "id": c_id,
            "name": name,
            "url": url,
            "status": status,
            "last_seen": last_seen,
            "active_incidents": incidents
        })
        
    return render_template("parent_dashboard.html", 
                           clients=processed_clients, 
                           total_incidents=total_incidents,
                           online_count=online_count,
                           total_clients=len(clients))

@app.route("/api/register_child", methods=["POST"])
def register_child():
    data = request.json
    client_name = data.get("client_name")
    url = data.get("url")
    active_incidents = data.get("active_incidents", 0)
    
    if not client_name or not url:
        return jsonify({"error": "Missing client_name or url"}), 400
        
    try:
        success = register_or_update_client(client_name, url, active_incidents)
        if not success:
            print(f"[REJECTED] Heartbeat from blacklisted client: {client_name}")
            return jsonify({"error": "Client is blacklisted and cannot register."}), 403
            
        print(f"[HEARTBEAT] Received from {client_name} ({url}) - Incidents: {active_incidents}")
        return jsonify({"status": "Success"})
    except Exception as e:
        print(f"[ERROR] Failed to register child: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/client/delete/<int:client_id>", methods=["POST"])
def remove_client(client_id):
    try:
        # Get client name before blacklisting
        clients = get_all_clients()
        client = next((c for c in clients if c[0] == client_id), None)
        if client:
            client_name = client[1]
            from parent_database import blacklist_client
            blacklist_client(client_name)
            return jsonify({"status": "Permanently Blacklisted"})
        else:
            return jsonify({"error": "Client not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/client/toggle_status/<int:client_id>", methods=["POST"])
def toggle_status(client_id):
    data = request.json
    is_disabled = data.get("disabled", False)
    try:
        toggle_client_status(client_id, is_disabled)
        return jsonify({"status": "Updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/client/push_update/<int:client_id>", methods=["POST"])
def push_update(client_id):
    # Find client URL
    clients = get_all_clients()
    client = next((c for c in clients if c[0] == client_id), None)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    client_url = client[2]
    
    # Simple push: Zip all .py files and send to client
    try:
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk('.'):
                if 'venv' in root or '.git' in root or '__pycache__' in root:
                    continue
                for file in files:
                    if file.endswith('.py') or file.endswith('.html') or file.endswith('.css'):
                        zf.write(os.path.join(root, file))
        
        memory_file.seek(0)
        
        response = requests.post(f"{client_url}/api/update", 
                                 files={'update': ('update.zip', memory_file, 'application/zip')},
                                 headers={"X-Update-Token": "secret-admin-token"})
        
        if response.status_code == 200:
            return jsonify({"status": "Update pushed successfully"})
        else:
            return jsonify({"error": f"Client update failed: {response.text}"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
