import os
import re
from flask import Flask, url_for

app = Flask(__name__, template_folder='c:/Users/altha/OneDrive/Desktop/MediQueue/templates', static_folder='c:/Users/altha/OneDrive/Desktop/MediQueue/static')

def check_static_assets():
    print("Checking static assets...")
    static_dir = app.static_folder
    missing_assets = []
    
    # Walk through templates and find static references
    template_dir = app.template_folder
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Find url_for('static', filename='...')
                    matches = re.findall(r"url_for\('static',\s*filename=['\"]([^'\"]+)['\"]\)", content)
                    for match in matches:
                        asset_path = os.path.join(static_dir, match)
                        if not os.path.exists(asset_path):
                            missing_assets.append((file, match))
    
    if missing_assets:
        print("Missing static assets found:")
        for template, asset in missing_assets:
            print(f"  Template: {template}, Asset: {asset}")
    else:
        print("No missing static assets found.")

if __name__ == "__main__":
    check_static_assets()
