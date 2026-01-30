
import os
import re

def is_mojibake(text):
    # Heuristic: Check for common mojibake characters in this project
    # 縺 (E3 81), 繝 (E3 83), 縲 (E3 80)
    mojibake_chars = ['縺', '繝', '縲', '螳', '蜃', '蜀', '逋']
    count = sum(text.count(c) for c in mojibake_chars)
    # If we find more than a few, it's likely mojibake
    return count > 2

def try_repair(text):
    try:
        # The standard fix logic
        repaired = text.encode('cp932').decode('utf-8')
        return repaired, True
    except:
        # If it fails, try a more surgical approach for the whole string
        # Process by lines?
        lines = text.splitlines()
        new_lines = []
        changed = False
        for line in lines:
            try:
                # Try to fix the whole line
                fixed_line = line.encode('cp932').decode('utf-8')
                new_lines.append(fixed_line)
                if fixed_line != line:
                    changed = True
            except:
                # If line fails, try to fix only non-ascii parts of the line
                # This is tricky because mojibake is often multi-char
                # Let's try to fix contiguous non-ascii segments
                segments = re.split(r'([^\x00-\x7F]+)', line)
                fixed_segments = []
                for seg in segments:
                    if not seg or all(ord(c) < 128 for c in seg):
                        fixed_segments.append(seg)
                    else:
                        try:
                            fixed_seg = seg.encode('cp932').decode('utf-8')
                            fixed_segments.append(fixed_seg)
                            changed = True
                        except:
                            # If even that fails, we can't fix this segment reliably
                            # Maybe try character by character? (Usually doesn't work for misalignment)
                            fixed_segments.append(seg)
                new_lines.append("".join(fixed_segments))
        
        return "\n".join(new_lines), changed

def process_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return False

    if not is_mojibake(content):
        # Even if not "highly" likely, try a silent repair check
        # But only if it's in the business folder
        if 'business' not in path and 'administration' not in path:
            return False

    repaired, changed = try_repair(content)
    
    if changed and repaired != content:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(repaired)
            print(f"Repaired: {path}")
            return True
        except Exception as e:
            print(f"Error writing {path}: {e}")
            return False
    return False

def main():
    root_dirs = [
        'business/templates',
        'administration/templates',
        'jobs/templates',
        'accounts/templates',
        'templates'
    ]
    
    total = 0
    repaired_count = 0
    
    for rdir in root_dirs:
        abs_rdir = os.path.join(os.getcwd(), rdir)
        if not os.path.exists(abs_rdir):
            continue
            
        for root, dirs, files in os.walk(abs_rdir):
            for file in files:
                if file.endswith('.html'):
                    total += 1
                    if process_file(os.path.join(root, file)):
                        repaired_count += 1
                        
    print(f"\nScan completed.")
    print(f"Total HTML files checked: {total}")
    print(f"Total files repaired: {repaired_count}")

if __name__ == "__main__":
    main()
