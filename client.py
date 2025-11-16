import requests
import os

# --- 1. CONFIGURATION ---
BASE_URL = "http://127.0.0.1:5000"
UPLOAD_URL = f"{BASE_URL}/upload"
DOWNLOAD_URL = f"{BASE_URL}/download"
SHARE_URL = f"{BASE_URL}/share"
EDIT_URL = f"{BASE_URL}/edit"
MY_FILES_URL = f"{BASE_URL}/myfiles"

USER_1_ID = "1"
USER_2_ID = "2"
USER_2_USERNAME = "user2"

# Test files
FILE_V1_NAME = "file_v1.txt"
FILE_V1_CONTENT = "This is Version 1, uploaded by User 1."

FILE_V2_NAME = "file_v2.txt"
FILE_V2_CONTENT = "This is Version 2, edited by User 2."

DOWNLOADED_FILENAME = "downloaded_final.txt"

# --- HELPER FUNCTION ---
def list_files(user_id, step_name):
    print(f"\n--- {step_name} (User {user_id}) ---")
    params = {'user_id': user_id}
    response = requests.get(MY_FILES_URL, params=params)
    
    if response.status_code != 200:
        print(f"Failed to list files: {response.json()}")
        return
        
    files = response.json()
    if not files:
        print("User has no files.")
    else:
        print("User's files:")
        for f in files:
            print(f"  - ID: {f['file_id']}, Name: {f['filename']}, Access: {f['access']}")
    return files

def run_test():
    try:
        # --- 2. CREATE FAKE FILES ---
        with open(FILE_V1_NAME, "w") as f: f.write(FILE_V1_CONTENT)
        with open(FILE_V2_NAME, "w") as f: f.write(FILE_V2_CONTENT)

        # --- 3. LIST FILES (User 1 - Before Upload) ---
        list_files(USER_1_ID, "0. LIST FILES (Before Upload)")

        # --- 4. UPLOAD (as User 1) ---
        print(f"\n--- 1. UPLOAD TEST (as User 1) ---")
        with open(FILE_V1_NAME, "rb") as f:
            files = {'file': (FILE_V1_NAME, f)}
            data = {'user_id': USER_1_ID}
            response = requests.post(UPLOAD_URL, files=files, data=data)
        
        if response.status_code != 201:
            print(f"UPLOAD FAILED!\n{response.json()}"); return
        
        file_id = response.json().get("file_id")
        print(f"Upload Successful. New file_id is: {file_id}")

        # --- 5. LIST FILES (User 1 - After Upload) ---
        list_files(USER_1_ID, "2. LIST FILES (After Upload)")

        # --- 6. SHARE (User 1 gives User 2 'view' access) ---
        print(f"\n--- 3. SHARE TEST (User 1 gives 'view' access) ---")
        share_data = {
            "user_id": USER_1_ID, "file_id": file_id,
            "target_username": USER_2_USERNAME, "access_level": "view"
        }
        response = requests.post(SHARE_URL, json=share_data)
        if response.status_code != 200:
            print(f"SHARE FAILED!\n{response.json()}"); return
        print("Share 'view' successful.")

        # --- 7. LIST FILES (User 2 - After Share) ---
        list_files(USER_2_ID, "4. LIST FILES (User 2)")

        # --- 8. EDIT ATTEMPT (as User 2 - with 'view' access) ---
        print(f"\n--- 5. EDIT TEST (as User 2 - should FAIL) ---")
        with open(FILE_V2_NAME, "rb") as f:
            files = {'file': (FILE_V2_NAME, f)}
            data = {'user_id': USER_2_ID, 'file_id': file_id}
            response = requests.post(EDIT_URL, files=files, data=data)
            
        if response.status_code == 403:
            print("SUCCESS: Edit was correctly DENIED (403).")
        else:
            print(f"FAILURE: Edit was allowed (Status {response.status_code})."); return

        # --- 9. UPGRADE PERMISSION (User 1 gives User 2 'EDIT' access) ---
        print(f"\n--- 6. UPGRADE SHARE TEST (User 1 gives 'edit' access) ---")
        share_data["access_level"] = "edit" # Change access level
        response = requests.post(SHARE_URL, json=share_data)
        if response.status_code != 200:
            print(f"SHARE UPGRADE FAILED!\n{response.json()}"); return
        print("Share 'edit' successful.")
        
        # --- 10. EDIT ATTEMPT (as User 2 - with 'edit' access) ---
        print(f"\n--- 7. EDIT TEST (as User 2 - should SUCCEED) ---")
        with open(FILE_V2_NAME, "rb") as f:
            files = {'file': (FILE_V2_NAME, f)}
            data = {'user_id': USER_2_ID, 'file_id': file_id}
            response = requests.post(EDIT_URL, files=files, data=data)

        if response.status_code != 200:
            print(f"EDIT FAILED!\n{response.json()}"); return
        print("SUCCESS: Edit was successful!")

        # --- 11. FINAL VERIFICATION (User 1 downloads the new version) ---
        print(f"\n--- 8. VERIFICATION (User 1 downloads User 2's edit) ---")
        params = {'user_id': USER_1_ID, 'file_id': file_id}
        response = requests.get(DOWNLOAD_URL, params=params)
        
        if response.status_code != 200:
            print(f"DOWNLOAD FAILED!\n{response.json()}"); return
        
        with open(DOWNLOADED_FILENAME, "wb") as f:
            f.write(response.content)
            
        with open(DOWNLOADED_FILENAME, "r") as f:
            downloaded_content = f.read()
        
        if downloaded_content == FILE_V2_CONTENT:
            print(f"SUCCESS! Downloaded file content matches User 2's edit.")
        else:
            print(f"FAILURE! File content does not match.")

    except requests.exceptions.ConnectionError:
        print("\n--- ERROR ---")
        print("Could not connect to the server. Is app.py running?")
    except Exception as e:
        print(f"\n--- AN ERROR OCCURRED ---")
        print(e)
    
    finally:
        # --- 12. CLEANUP ---
        for f in [FILE_V1_NAME, FILE_V2_NAME, DOWNLOADED_FILENAME]:
            if os.path.exists(f):
                os.remove(f)
        print(f"\nCleaned up test files.")

if __name__ == "__main__":
    run_test()