
import os

file_path = r'c:\Users\altha\OneDrive\Desktop\MediQueue\templates\dashboard_base.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
inserted = False
for line in lines:
    new_lines.append(line)
    if 'Departments' in line and not inserted:
        # Check if next line is closing tag
        idx = lines.index(line)
        if idx + 1 < len(lines) and '</a>' in lines[idx+1]:
            # We are at the right place, but we want to insert AFTER the </a>
            pass
        
    if 'Departments' in line:
        # We found the line with Departments. The next line should be </a>.
        # Let's just look for the closing </a> tag that follows Departments
        pass

# Simpler approach: Find the exact block and replace it
content = "".join(lines)
target = """                Departments
            </a>"""
replacement = """                Departments
            </a>
            <a href="{{ url_for('admin.manage_payments') }}"
                class="flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 {% if request.endpoint == 'admin.manage_payments' %}bg-gradient-to-r from-teal-50 to-emerald-50 text-teal-700 dark:from-teal-900/20 dark:to-emerald-900/20 dark:text-teal-300 border border-teal-100 dark:border-teal-800/50{% else %}text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/50 dark:hover:text-slate-200{% endif %}">
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Payments
            </a>"""

if target in content:
    new_content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully patched dashboard_base.html")
else:
    print("Target not found in dashboard_base.html")
    # Print a snippet to see what's wrong
    start = content.find("Departments")
    if start != -1:
        print(f"Found 'Departments' at {start}. Context:")
        print(repr(content[start-20:start+50]))
