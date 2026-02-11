
import os
import shutil
from pathlib import Path

def organize_icons():
    base_dir = r"C:\Users\info\Desktop\Nouveau dossier (2)\langflow_icons"
    extracted_dir = os.path.join(base_dir, "extracted")
    
    if not os.path.exists(extracted_dir):
        print("Extracted dir not found")
        return

    # Organize by prefix
    for filename in os.listdir(extracted_dir):
        if not filename.endswith('.svg'):
            continue
            
        # Extract prefix: "arrow-down-D7JjV53c.svg" -> "arrow"
        parts = filename.split('-')
        if len(parts) > 1:
            prefix = parts[0]
        else:
            prefix = "misc"
            
        target_dir = os.path.join(base_dir, "Lucide-Library", prefix)
        os.makedirs(target_dir, exist_ok=True)
        
        shutil.move(os.path.join(extracted_dir, filename), os.path.join(target_dir, filename))

    print("Icons organized by prefix in Lucide-Library folder")

    # Move known brand icons to a separate folder
    brand_dir = os.path.join(base_dir, "Brand-Icons")
    os.makedirs(brand_dir, exist_ok=True)
    
    # Simple list of brands we might have
    brands = ["Slack", "Wikipedia", "Google", "OpenAI", "Notion", "Github", "Gitlab", "Figma", "Dribbble"]
    
    # Re-scan Lucide-Library for these
    lucide_root = os.path.join(base_dir, "Lucide-Library")
    for root, dirs, files in os.walk(lucide_root):
        for f in files:
            for brand in brands:
                if brand.lower() in f.lower():
                    dest = os.path.join(brand_dir, f)
                    shutil.move(os.path.join(root, f), dest)
                    break

    # Clean up empty dirs in Lucide-Library
    for root, dirs, files in os.walk(lucide_root, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)

if __name__ == "__main__":
    organize_icons()
