import os

path = 'business/templates/business/Workers/worker_management.html'
if not os.path.exists(path):
    print(f"File not found: {path}")
    exit(1)

with open(path, 'rb') as f:
    data = f.read()

# Look for the "荳€閾ｴ" sequence in bytes
# 荳 in UTF-8: E8 B1 B8
# € in UTF-8: E2 82 AC
# 閾ｴ in UTF-8: E9 96 B4
# Wait, let's just search for the bytes we saw.

print("--- Byte level inspection of worker_management.html ---")
# Let's read it as utf-8 and find the line
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if '荳' in line or '閾ｴ' in line or '€' in line:
            print(f"Line {i+1}: {line.strip()}")
            print(f"Bytes: {line.encode('utf-8')}")
            
# Try to replace and see if it works
content = "".join(lines)
fixed = content.replace('荳€閾ｴ', '一致').replace('€・', '。')
if fixed != content:
    print("Found and replaced!")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(fixed)
else:
    print("Not found with literal match.")
    # Try atomic replacements
    fixed2 = content.replace('荳', '一').replace('閾ｴ', '致').replace('€', '').replace('・', '。')
    if fixed2 != content:
        print("Found with atomic replacements!")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fixed2)
