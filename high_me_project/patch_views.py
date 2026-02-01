import os

file_path = r'c:\Users\y_ootani\Documents\High_Me\high_Me-1\high_me_project\jobs\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_step1 = False
in_step2 = False

for i, line in enumerate(lines):
    # Check current class context (heuristic)
    if 'class StoreReviewStep1View' in line:
        in_step1 = True
        in_step2 = False
    elif 'class StoreReviewStep2View' in line:
        in_step1 = False
        in_step2 = True
    elif 'class ' in line:
        in_step1 = False
        in_step2 = False
    
    # Check for target lines in get_context_data
    if in_step1 and "context['application'] = application" in line:
        new_lines.append(line)
        new_lines.append("        context['step'] = 1\n")
    elif in_step2 and "context['application'] = application" in line:
        new_lines.append(line)
        new_lines.append("        context['step'] = 2\n")
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Patched views.py")
