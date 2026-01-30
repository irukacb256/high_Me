import os

BASE_DIR = r"c:\Users\y_ootani\Documents\High_Me\high_Me-1\high_me_project\business\templates\business"

mappings = {
    "Auth": ["signup.html", "account_register.html", "business_register.html", "verify_docs.html", "signup_complete.html", "login.html", "password_reset.html"],
    "Dashboard": ["dashboard.html", "portal.html"],
    "Jobs": ["template_list.html", "template_form.html", "template_detail.html", "template_delete_confirm.html", "job_create_form.html", "job_confirm.html", "job_posting_list.html", "job_posting_detail.html", "job_worker_list.html", "job_posting_visibility_edit.html"],
    "Workers": ["worker_detail.html", "worker_management.html", "checkin_management.html", "attendance_correction_list.html", "attendance_correction_detail.html", "worker_review_list.html", "worker_review_job_list.html"],
    "Messages": ["message_list.html", "message_detail.html"],
    "Store": ["store_setup.html", "group_management.html"],
    "Common": ["landing.html", "base_signup.html", "dashboard_base.html"],
}

# Fix extends refs and encoding
for folder, files in mappings.items():
    for f in files:
        path = os.path.join(BASE_DIR, folder, f)
        if os.path.exists(path):
            content = None
            encoding_used = 'utf-8'
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                try:
                    with open(path, 'r', encoding='cp932') as file:
                        content = file.read()
                    encoding_used = 'cp932'
                    print(f"Read {f} as cp932 (Shift-JIS)")
                except Exception as e:
                    print(f"Failed to read {f}: {e}")
                    continue
            
            if content:
                new_content = content.replace("extends 'business/base_signup.html'", "extends 'business/Common/base_signup.html'")
                new_content = new_content.replace('extends "business/base_signup.html"', 'extends "business/Common/base_signup.html"')
                new_content = new_content.replace("extends 'business/dashboard_base.html'", "extends 'business/Common/dashboard_base.html'")
                new_content = new_content.replace('extends "business/dashboard_base.html"', 'extends "business/Common/dashboard_base.html"')
                
                # Check for other potential bad extends
                if "extends 'business/" in new_content and "extends 'business/Common/" not in new_content:
                     # This logic is weak but good enough for specific targets
                     pass

                # Always rewrite as UTF-8 if it was CP932 OR content changed
                if encoding_used == 'cp932' or content != new_content:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    print(f"Updated {path} (Converted to UTF-8)")
