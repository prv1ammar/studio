import os

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='ascii', errors='ignore') as f:
            lines = f.readlines()
        
        # Remove empty lines if they are redundant (like every second line is empty)
        # But wait, that's risky. 
        # A better way: just replace double newlines with single ones IF they are exactly double.
        # Or just read as text and use splitlines() then join with single \n.
        
        with open(filepath, 'r', encoding='ascii', errors='ignore') as f:
            content = f.read()
        
        # Replace \r\n with \n first to normalize
        normalized = content.replace('\r\n', '\n')
        # If we have \n\n everywhere, it's doubled.
        # But we only want to fix it if it's REALLY doubled.
        # Actually, let's just use splitlines() and then join. 
        # But we need to keep intentional empty lines.
        # If it's doubled, then every other line is empty.
        
        lines = normalized.split('\n')
        if len(lines) > 1:
            # Check if all odd indices are empty (0-indexed: 1, 3, 5...)
            is_doubled = all(lines[i].strip() == '' for i in range(1, len(lines), 2))
            if is_doubled:
                fixed_lines = lines[::2]
                with open(filepath, 'w', encoding='ascii') as f:
                    f.write('\n'.join(fixed_lines))
                print(f"Fixed doubling in: {filepath}")
            else:
                # Just normalize to \n and write back
                with open(filepath, 'w', encoding='ascii') as f:
                    f.write(normalized)
                print(f"Normalized: {filepath}")
    except Exception as e:
        print(f"Failed to fix {filepath}: {e}")

def walk_and_fix(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                fix_file(os.path.join(root, file))

if __name__ == "__main__":
    target = r"c:\Users\PC\Desktop\studio V3.0.0\studio_clone\backend\app"
    walk_and_fix(target)
