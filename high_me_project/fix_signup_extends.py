import os

BASE_DIR = r"c:\Users\y_ootani\Documents\High_Me\high_Me-1\high_me_project\accounts\templates\Auth"

for filename in os.listdir(BASE_DIR):
    if filename.endswith(".html"):
        path = os.path.join(BASE_DIR, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "extends 'signup/signup_base.html'" in content or 'extends "signup/signup_base.html"' in content:
                new_content = content.replace("extends 'signup/signup_base.html'", "extends 'Auth/signup_base.html'")
                new_content = new_content.replace('extends "signup/signup_base.html"', 'extends "Auth/signup_base.html"')
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
