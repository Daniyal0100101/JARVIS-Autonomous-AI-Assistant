import subprocess
import sys
import os
import platform


def detect_requirements_file() -> str:
    """Choose the best requirements file: prefer 'Requirements/requirements.txt' then 'requirements.txt'."""
    candidates = [
        os.path.join("Requirements", "requirements.txt"),
        "requirements.txt",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No requirements file found. Expected 'Requirements/requirements.txt' or 'requirements.txt'.")


def read_lines_utf8(path: str):
    """Read file content robustly as UTF-8, falling back to 'latin-1' on decode issues."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.readlines()


def upgrade_pip_quietly():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Non-fatal
        pass


problematic_packages = []


def install_package(requirement_line: str):
    """Install a single requirement line with a retry using build isolation and no cache."""
    if not requirement_line or requirement_line.strip().startswith("#"):
        return
    req = requirement_line.strip()
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", req])
        print(f"Installed: {req}")
        return
    except subprocess.CalledProcessError:
        # Retry with build isolation
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--use-pep517", "--no-cache-dir", req])
            print(f"Installed on retry (PEP517): {req}")
            return
        except subprocess.CalledProcessError as e:
            print(f"Failed: {req} ({e})")
            problematic_packages.append(req)


def try_bulk_install(path: str) -> bool:
    """Attempt bulk installation with pip -r. Return True if succeeded, else False."""
    try:
        print(f"Attempting bulk install from: {path}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", path])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Bulk install failed: {e}. Falling back to line-by-line.")
        return False


def guidance_for(problem: str) -> str:
    """Return platform-specific guidance for known tricky packages."""
    sysname = platform.system()
    pkg = problem.lower()
    if "pyaudio" in pkg:
        if sysname == "Linux":
            return "Hint: install PortAudio dev libs: 'sudo apt install portaudio19-dev' then pip install PyAudio."
        elif sysname == "Darwin":
            return "Hint: 'brew install portaudio' then 'pip install PyAudio'."
        else:
            return "Hint: install PyAudio wheel for your Python version if build fails."
    if "opencv" in pkg:
        return "Hint: opencv may require system libs. Try 'pip install opencv-python-headless' if GUI not needed."
    if "mediapipe" in pkg:
        return "Hint: mediapipe wheels vary by platform. Ensure Python version compatibility (3.10+)."
    if "torch" in pkg or "torchvision" in pkg:
        return "Hint: visit pytorch.org for the correct command for your OS/Python/CUDA."
    if "pygame" in pkg:
        if sysname == "Linux":
            return "Hint: ensure SDL dependencies: 'sudo apt install libsdl2-dev'."
    return ""


def install_all_packages(path: str):
    if not os.path.exists(path):
        print(f"Requirements file not found: {path}")
        sys.exit(1)

    # Try bulk install first
    if try_bulk_install(path):
        print("All packages installed via bulk install.")
        return

    # Fallback: line-by-line
    lines = read_lines_utf8(path)
    for line in lines:
        req = line.strip()
        if not req or req.startswith("#"):
            continue
        print(f"Installing {req}...")
        install_package(req)

    print("\nInstallation attempt complete.")
    if problematic_packages:
        print("The following packages had issues:")
        for p in problematic_packages:
            tip = guidance_for(p)
            if tip:
                print(f"- {p}\n  {tip}")
            else:
                print(f"- {p}")
    else:
        print("All packages installed successfully.")

    # Optional: pip check to validate installed package metadata
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "check"])
    except subprocess.CalledProcessError:
        print("Warning: 'pip check' reported issues with package dependencies.")


if __name__ == "__main__":
    upgrade_pip_quietly()
    req_path = detect_requirements_file()
    print(f"Using requirements file: {req_path}")
    install_all_packages(req_path)
