"""
Clean Packaging Utility for OAuth Navigator.
Creates a verified production distribution zip excluding all virtual environments,
bytecode, temporary files, runtime stores, and secrets.
"""
import os
import sys
import zipfile

ROOT_DIR = r"D:\Composio"
OUTPUT_ZIP = os.path.join(ROOT_DIR, "oauth_navigator_clean.zip")

EXCLUDED_DIRS = {
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".idea",
    ".vscode",
}

EXCLUDED_FILES = {
    ".env",
    ".env.local",
    "guides_store.json",
    "oauth_navigator_clean.zip",
}

EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".tmp",
    ".log",
}


def should_exclude(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")

    # Check directory exclusion
    for part in parts[:-1]:
        if part in EXCLUDED_DIRS:
            return True

    # Check filename exclusion
    filename = parts[-1]
    if filename in EXCLUDED_FILES or filename in EXCLUDED_DIRS:
        return True

    if filename.startswith(".env") and not filename.endswith(".example"):
        return True

    _, ext = os.path.splitext(filename)
    if ext.lower() in EXCLUDED_EXTENSIONS:
        return True

    if filename.endswith(".json.tmp"):
        return True

    return False


def create_clean_zip():
    print(f"Creating clean distribution archive: {OUTPUT_ZIP}")
    included_count = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Prune excluded directories in-place so os.walk doesn't recurse into them
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, ROOT_DIR)

                if should_exclude(rel_path):
                    continue

                zf.write(abs_path, rel_path)
                included_count += 1

    print(f"Archive created with {included_count} files.")

    # Verification of archive contents
    print("Verifying archive safety constraints...")
    forbidden_found = []
    has_env_example = False
    has_seed_guides = False

    with zipfile.ZipFile(OUTPUT_ZIP, "r") as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            parts = name.split("/")

            # Check for forbidden entries
            if any(p in EXCLUDED_DIRS for p in parts):
                forbidden_found.append(f"Forbidden directory in path: {name}")

            if parts[-1] in EXCLUDED_FILES or parts[-1].endswith(".pyc") or parts[-1].endswith(".tmp"):
                forbidden_found.append(f"Forbidden file: {name}")

            if parts[-1] == ".env" or (parts[-1].startswith(".env") and not parts[-1].endswith(".example")):
                forbidden_found.append(f"Secret .env file found: {name}")

            if parts[-1] == ".env.example":
                has_env_example = True

            if parts[-1] == "seed_guides.json":
                has_seed_guides = True

    if forbidden_found:
        print("VERIFICATION FAILED: Forbidden items found in archive:")
        for item in forbidden_found:
            print(f"  - {item}")
        sys.exit(1)

    if not has_env_example:
        print("VERIFICATION FAILED: .env.example missing from archive!")
        sys.exit(1)

    if not has_seed_guides:
        print("VERIFICATION FAILED: seed_guides.json missing from archive!")
        sys.exit(1)

    print("VERIFICATION PASSED: Clean distribution archive verified with 0 secrets and 0 forbidden files.")


if __name__ == "__main__":
    create_clean_zip()

