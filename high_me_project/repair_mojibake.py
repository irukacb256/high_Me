import os

def repair_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # The corruption happened by taking UTF-8 bytes and decoding them as CP932.
        # To reverse: Encode current string (the mojibake) as CP932 to get back original UTF-8 bytes,
        # then decode those bytes as UTF-8.
        repaired = content.encode('cp932').decode('utf-8')
        
        if repaired != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(repaired)
            return True
    except Exception as e:
        print(f"Skip {path}: {e}")
        return False

def main():
    target_dir = 'business/templates/business'
    repaired_count = 0
    total_count = 0
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.html'):
                total_count += 1
                if repair_file(os.path.join(root, file)):
                    repaired_count += 1
                    print(f"Repaired: {os.path.join(root, file)}")
    
    print(f"Total files: {total_count}")
    print(f"Repaired files: {repaired_count}")

if __name__ == "__main__":
    main()
