import zipfile
import os

zip_path = r"D:\Composio\oauth_navigator_clean.zip"
print(f"Inspecting: {zip_path}")
assert os.path.exists(zip_path), "ZIP does not exist"

with zipfile.ZipFile(zip_path, "r") as zf:
    infolist = zf.infolist()
    print(f"Total files: {len(infolist)}")
    forbidden = [".venv", "__pycache__", ".pytest_cache", ".git", ".pyc", "guides_store.json", ".log"]
    found_forbidden = []
    names = []
    has_env_example = False
    
    for info in infolist:
        name = info.filename.replace("\\", "/")
        names.append((name, info.file_size))
        
        # Check .env
        if (name == ".env" or name.endswith("/.env")) and not name.endswith(".env.example"):
            found_forbidden.append(name)
            
        for f in forbidden:
            if f in name:
                found_forbidden.append(name)
                
        if name.endswith(".env.example"):
            has_env_example = True
            
    print("\n--- FILE LIST IN ARCHIVE ---")
    for n, s in sorted(names):
        print(f"{s:>8} bytes | {n}")
    print("----------------------------\n")
    print(f"Total count: {len(names)}")
    print(f"Forbidden items found: {found_forbidden}")
    print(f".env.example present: {has_env_example}")

