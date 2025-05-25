import subprocess
import sys, os

file_path = "Requirements/requirements.txt"

def encoder(file_path):
    import chardet

    # Detect encoding
    with open(file_path, "rb") as f:
        raw_data = f.read()
        encoding_info = chardet.detect(raw_data)
        detected_encoding = encoding_info["encoding"]

    print(f"Detected Encoding: {detected_encoding}")

    # Convert to UTF-8 if needed
    if detected_encoding and detected_encoding.lower() != "utf-8":
        with open(file_path, "r", encoding=detected_encoding) as f:
            content = f.read()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Converted {file_path} to UTF-8 encoding.")
    else:
        print(f"{file_path} is already UTF-8 encoded.")

# List to keep track of problematic packages
problematic_packages = []

def install_package(package_name):
    try:
        # Installing a single package using pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"{package_name} installed successfully.")
    except subprocess.CalledProcessError:
        # Append the package to problematic packages list and continue
        print(f"Error occurred while installing {package_name}. Skipping this package.")
        problematic_packages.append(package_name)

def install_all_packages(file_path):
    if os.path.exists(file_path):
        try:
            # Open and read the requirements.txt file
            with open(file_path, "r") as file:
                packages = file.readlines()
            
            # Install each package one by one
            for package in packages:
                package = package.strip()  # Remove any leading/trailing whitespace
                if package:  # Skip any empty lines
                    print(f"Installing {package}...")
                    install_package(package)
                    
            print("All packages attempted.")
            
            # Report problematic packages at the end
            if problematic_packages:
                print("\nThe following packages had issues during installation:")
                for package in problematic_packages:
                    print(f"- {package}")
            else:
                print("\nAll packages installed successfully.")
            
        except Exception as e:
            print(f"An error: ", str(e))
            sys.exit(1)
    else:
        print(f"Sorry but file({file_path}). Does not exist.")

if __name__ == "__main__":
    # encoder(file_path)
    install_all_packages(file_path)