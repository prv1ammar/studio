import os

def clean_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Decode as utf-8, but replace errors to see what we have
        # Then encode back to strictly ASCII or just remove non-ascii
        text = content.decode('utf-8', errors='ignore')
        
        # Remove common emojis and garbage characters seen in the logs
        # We can just filter for printable ASCII (32-126) plus newlines/tabs
        cleaned_text = "".join(c for c in text if ord(c) < 128)
        
        with open(filepath, 'w', encoding='ascii') as f:
            f.write(cleaned_text)
        print(f"Cleaned: {filepath}")
    except Exception as e:
        print(f"Failed to clean {filepath}: {e}")

def walk_and_clean(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                clean_file(os.path.join(root, file))

if __name__ == "__main__":
    target = r"c:\Users\PC\Desktop\studio V3.0.0\studio_clone\backend\app"
    walk_and_clean(target)
