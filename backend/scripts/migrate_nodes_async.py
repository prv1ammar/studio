import os

root_dirs = [
    r'backend/app/nodes/integrations',
    r'backend/app/nodes/google'
]

def migrate_nodes():
    for root_dir in root_dirs:
        for filename in os.listdir(root_dir):
            if filename.endswith('.py'):
                path = os.path.join(root_dir, filename)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace self.get_credential( with await self.get_credential(
                if 'self.get_credential(' in content and 'await self.get_credential(' not in content:
                    print(f"Migrating {path}...")
                    new_content = content.replace('self.get_credential(', 'await self.get_credential(')
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

if __name__ == "__main__":
    migrate_nodes()
