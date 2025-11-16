import sqlite3
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import uuid
import io

# --- 1. CONFIGURATION ---
DATABASE_FILE = "project.db"
UPLOAD_FOLDER = "uploads"

app = Flask(__name__)
CORS(app) 

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_filename TEXT NOT NULL,
        server_filename TEXT NOT NULL,
        owner_id INTEGER NOT NULL,
        encryption_key TEXT NOT NULL,
        locked_by_user_id INTEGER DEFAULT NULL, 
        FOREIGN KEY (owner_id) REFERENCES users (id),
        FOREIGN KEY (locked_by_user_id) REFERENCES users (id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        file_id INTEGER NOT NULL,
        access_level TEXT NOT NULL,  -- 'view' or 'edit'
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (file_id) REFERENCES files (id),
        UNIQUE(user_id, file_id)
    );
    """)
    
    try:
        cursor.execute("INSERT INTO users (username) VALUES ('user1')")
        cursor.execute("INSERT INTO users (username) VALUES ('user2')")
    except sqlite3.IntegrityError:
        pass # Users already exist
        
    conn.commit()
    conn.close()

# --- 3. HELPER FUNCTION: PERMISSION CHECK ---
def check_permission(user_id, file_id, required_level):
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT access_level FROM permissions WHERE user_id = ? AND file_id = ?",
        (user_id, file_id)
    )
    result = cursor.fetchone()
    conn.close()
    if not result: return False
    access_level = result[0]
    if access_level == 'edit': return True
    if access_level == 'view' and required_level == 'view': return True
    return False

# --- 4. UPLOAD ENDPOINT ---
@app.route('/upload', methods=['POST'])
def upload_file():
    # (This code is identical, just changed db connection)
    if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    user_id = request.form.get('user_id')
    if file.filename == '' or not user_id: return jsonify({"error": "Missing file or user_id"}), 400

    try:
        file_key = get_random_bytes(16)
        original_filename = file.filename
        server_filename = str(uuid.uuid4())
        server_filepath = os.path.join(UPLOAD_FOLDER, server_filename)

        file_content = file.read()
        cipher = AES.new(file_key, AES.MODE_CBC)
        iv = cipher.iv
        padded_content = pad(file_content, AES.block_size)
        encrypted_content = cipher.encrypt(padded_content)
        encrypted_data_with_iv = iv + encrypted_content

        with open(server_filepath, "wb") as f: f.write(encrypted_data_with_iv)

        conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (original_filename, server_filename, owner_id, encryption_key) VALUES (?, ?, ?, ?)",
            (original_filename, server_filename, user_id, file_key.hex())
        )
        conn.commit()
        file_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO permissions (user_id, file_id, access_level) VALUES (?, ?, ?)",
            (user_id, file_id, "edit")
        )
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"File '{original_filename}' uploaded.", "file_id": file_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 5. DOWNLOAD ENDPOINT ---
@app.route('/download', methods=['GET'])
def download_file():
    # (This code is identical, just changed db connection)
    user_id = request.args.get('user_id')
    file_id = request.args.get('file_id')
    if not user_id or not file_id: return jsonify({"error": "Missing user_id or file_id"}), 400
    
    try:
        if not check_permission(user_id, file_id, 'view'):
            return jsonify({"error": "Access Denied. You do not have 'view' permission."}), 403

        conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT original_filename, server_filename, encryption_key FROM files WHERE id = ?", (file_id,)
        )
        file_info = cursor.fetchone()
        conn.close()
        if not file_info: return jsonify({"error": "File not found"}), 404
            
        original_filename, server_filename, file_key_hex = file_info
        file_key = bytes.fromhex(file_key_hex)
        server_filepath = os.path.join(UPLOAD_FOLDER, server_filename)

        with open(server_filepath, "rb") as f: encrypted_data_with_iv = f.read()
        
        iv = encrypted_data_with_iv[:16]
        ciphertext = encrypted_data_with_iv[16:]
        cipher = AES.new(file_key, AES.MODE_CBC, iv)
        decrypted_padded_content = cipher.decrypt(ciphertext)
        decrypted_content = unpad(decrypted_padded_content, AES.block_size)

        return send_file(
            io.BytesIO(decrypted_content),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=original_filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 6. SHARE ENDPOINT ---
@app.route('/share', methods=['POST'])
def share_file():
    # (This code is identical, just changed db connection)
    try:
        data = request.json
        sharer_user_id = data.get('user_id')
        file_id = data.get('file_id')
        target_username = data.get('target_username')
        access_level = data.get('access_level')

        if not all([sharer_user_id, file_id, target_username, access_level]):
            return jsonify({"error": "Missing required fields"}), 400
        if access_level not in ['view', 'edit']:
            return jsonify({"error": "Invalid access level."}), 400
        if not check_permission(sharer_user_id, file_id, 'edit'):
            return jsonify({"error": "Access Denied. Only 'edit' users can share."}), 403

        conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (target_username,))
        target_user = cursor.fetchone()
        if not target_user:
            conn.close()
            return jsonify({"error": f"User '{target_username}' not found."}), 404
        target_user_id = target_user[0]
        
        cursor.execute(
            """
            INSERT INTO permissions (user_id, file_id, access_level) VALUES (?, ?, ?)
            ON CONFLICT(user_id, file_id) DO UPDATE SET access_level = excluded.access_level
            """,
            (target_user_id, file_id, access_level)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"File shared with {target_username}."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 7. EDIT ENDPOINT (UPDATED) ---
@app.route('/edit', methods=['POST'])
def edit_file():
    if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    user_id = request.form.get('user_id')
    file_id = request.form.get('file_id')
    if not all([file, user_id, file_id]): return jsonify({"error": "Missing fields"}), 400

    try:
        # 1. Check for 'edit' permission
        if not check_permission(user_id, file_id, 'edit'):
            return jsonify({"error": "Access Denied. You do not have 'edit' permission."}), 403

        conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        # 2. Check for 'lock'
        cursor.execute(
            "SELECT server_filename, encryption_key, locked_by_user_id FROM files WHERE id = ?", (file_id,)
        )
        file_info = cursor.fetchone()
        if not file_info:
            conn.close()
            return jsonify({"error": "File not found"}), 404
        
        server_filename, file_key_hex, locked_by = file_info
        
        if locked_by != int(user_id):
            conn.close()
            return jsonify({"error": "Access Denied. You must lock the file before editing."}), 403

        # 3. User has permission AND the lock, proceed with edit
        file_key = bytes.fromhex(file_key_hex)
        server_filepath = os.path.join(UPLOAD_FOLDER, server_filename)
        
        file_content = file.read()
        cipher = AES.new(file_key, AES.MODE_CBC)
        iv = cipher.iv
        padded_content = pad(file_content, AES.block_size)
        encrypted_content = cipher.encrypt(padded_content)
        encrypted_data_with_iv = iv + encrypted_content

        with open(server_filepath, "wb") as f: f.write(encrypted_data_with_iv)
        
        # 4. Automatically unlock the file after successful edit
        cursor.execute(
            "UPDATE files SET locked_by_user_id = NULL WHERE id = ?", (file_id,)
        )
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"File {file_id} updated and unlocked."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 8. LIST FILES ENDPOINT (UPDATED) ---
@app.route('/myfiles', methods=['GET'])
def get_my_files():
    user_id = request.args.get('user_id')
    if not user_id: return jsonify({"error": "Missing user_id"}), 400
    
    try:
        conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        # Join with users table to get the username of the person who locked it
        cursor.execute(
            """
            SELECT f.id, f.original_filename, p.access_level, f.locked_by_user_id, u.username
            FROM files f
            JOIN permissions p ON f.id = p.file_id
            LEFT JOIN users u ON f.locked_by_user_id = u.id
            WHERE p.user_id = ?
            """,
            (user_id,)
        )
        files_data = cursor.fetchall()
        conn.close()
        
        my_files = []
        for row in files_data:
            my_files.append({
                "file_id": row[0],
                "filename": row[1],
                "access": row[2],
                "locked_by_id": row[3], # e.g., 2
                "locked_by_name": row[4]  # e.g., "user2"
            })
        return jsonify(my_files), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 9. NEW: LOCK FILE ENDPOINT ---
@app.route('/lock', methods=['POST'])
def lock_file():
    data = request.json
    user_id = data.get('user_id')
    file_id = data.get('file_id')
    
    if not user_id or not file_id:
        return jsonify({"error": "Missing user_id or file_id"}), 400
    
    # 1. Check for 'edit' permission
    if not check_permission(user_id, file_id, 'edit'):
        return jsonify({"error": "Access Denied. Only 'edit' users can lock files."}), 403

    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    
    # 2. Check if file is already locked
    cursor.execute(
        "SELECT locked_by_user_id, u.username FROM files f LEFT JOIN users u ON f.locked_by_user_id = u.id WHERE f.id = ?", (file_id,)
    )
    file_info = cursor.fetchone()
    
    if not file_info:
        conn.close()
        return jsonify({"error": "File not found"}), 404
        
    locked_by, locker_name = file_info
    
    if locked_by is not None:
        conn.close()
        if locked_by == int(user_id):
            return jsonify({"success": True, "message": "You already have this file locked."})
        return jsonify({"error": f"File is already locked by {locker_name}."}), 403
    
    # 3. File is free, lock it
    cursor.execute(
        "UPDATE files SET locked_by_user_id = ? WHERE id = ?", (user_id, file_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "File locked successfully."}), 200

# --- 10. NEW: UNLOCK FILE ENDPOINT ---
@app.route('/unlock', methods=['POST'])
def unlock_file():
    data = request.json
    user_id = data.get('user_id')
    file_id = data.get('file_id')
    
    if not user_id or not file_id:
        return jsonify({"error": "Missing user_id or file_id"}), 400
        
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    
    # Check if file is locked *by this user*
    cursor.execute(
        "SELECT locked_by_user_id FROM files WHERE id = ?", (file_id,)
    )
    file_info = cursor.fetchone()
    
    if not file_info:
        conn.close()
        return jsonify({"error": "File not found"}), 404
        
    locked_by = file_info[0]
    
    if locked_by != int(user_id):
        conn.close()
        return jsonify({"error": "Access Denied. You cannot unlock a file locked by another user."}), 403
        
    # 2. Unlock it
    cursor.execute(
        "UPDATE files SET locked_by_user_id = NULL WHERE id = ?", (file_id,)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "File unlocked."}), 200

# --- 11. SCRIPT EXECUTION ---
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)