import subprocess

def get_ram():
    result = subprocess.run(["free", "-h"], capture_output=True, text=True)
    return result.stdout