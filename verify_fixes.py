import os
import re

def verify_fixes():
    base_html_path = r'c:\Users\altha\OneDrive\Desktop\MediQueue\templates\base.html'
    doctors_html_path = r'c:\Users\altha\OneDrive\Desktop\MediQueue\templates\admin\doctors.html'
    admin_routes_path = r'c:\Users\altha\OneDrive\Desktop\MediQueue\routes\admin.py'

    # 1. Verify Developer Name in base.html
    with open(base_html_path, 'r', encoding='utf-8') as f:
        base_content = f.read()
    
    if "Developed by Althaf" in base_content:
        print("[PASS] Developer Name found in base.html")
    else:
        print("[FAIL] Developer Name NOT found in base.html")

    # 2. Verify CSRF Token in base.html
    if '<meta name="csrf-token" content="{{ csrf_token() }}">' in base_content:
        print("[PASS] CSRF Meta Tag found in base.html")
    else:
        print("[FAIL] CSRF Meta Tag NOT found in base.html")

    # 3. Verify Edit Modal in doctors.html
    with open(doctors_html_path, 'r', encoding='utf-8') as f:
        doctors_content = f.read()
    
    if 'id="editDoctorModal"' in doctors_content:
        print("[PASS] Edit Doctor Modal found in doctors.html")
    else:
        print("[FAIL] Edit Doctor Modal NOT found in doctors.html")
        
    if 'openEditModal' in doctors_content:
        print("[PASS] openEditModal JS function found in doctors.html")
    else:
        print("[FAIL] openEditModal JS function NOT found in doctors.html")

    # 4. Verify edit_doctor route in admin.py
    with open(admin_routes_path, 'r', encoding='utf-8') as f:
        admin_content = f.read()
        
    if '@admin_bp.route(\'/doctors/<int:doctor_id>/edit\', methods=[\'POST\'])' in admin_content:
        print("[PASS] edit_doctor route found in admin.py")
    else:
        print("[FAIL] edit_doctor route NOT found in admin.py")

if __name__ == "__main__":
    verify_fixes()
