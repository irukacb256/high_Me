import os
import re

def rename_project():
    root_dir = r"c:\Users\y_ootani\Documents\High_Me\high_Me-1\high_me_project"
    extensions = {".html", ".css", ".py"}
    
    # regex patterns
    patterns = [
        (re.compile(r'High Me'), 'High Me'),
        (re.compile(r'>High Me<'), '>High Me<'),
        (re.compile(r'(?<![a-zA-Z])High Me(?![a-zA-Z])'), 'High Me'),
        (re.compile(r'High Me'), 'High Me')
    ]

    for root, dirs, files in os.walk(root_dir):
        if ".gemini" in root or "venv" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = content
                    for pattern, replacement in patterns:
                        new_content = pattern.sub(replacement, new_content)
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Updated: {filepath}")
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    rename_project()
