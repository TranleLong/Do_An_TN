import os

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return
    
    # Border & Bg colors
    content = content.replace("rgba(255, 255, 255, 0.05)", "rgba(0, 0, 0, 0.05)")
    content = content.replace("rgba(255,255,255,0.05)", "rgba(0,0,0,0.05)")
    
    content = content.replace("rgba(255, 255, 255, 0.02)", "rgba(0, 0, 0, 0.02)")
    
    content = content.replace("rgba(255, 255, 255, 0.1)", "rgba(0, 0, 0, 0.1)")
    content = content.replace("rgba(255,255,255,0.1)", "rgba(0,0,0,0.1)")

    # Login gradients & shadow
    content = content.replace("#3d2b0e", "#e0f2fe")
    content = content.replace("0 25px 50px -12px rgba(0, 0, 0, 0.5)", "0 25px 50px -12px rgba(0, 0, 0, 0.15)")
    
    # Table header bg (was rgba(0,0,0,0.2) in dark mode, make it rgba(0,0,0,0.04) in light mode)
    content = content.replace("rgba(0, 0, 0, 0.2)", "rgba(0, 0, 0, 0.04)")
    content = content.replace("rgba(0,0,0,0.2)", "rgba(0,0,0,0.04)")
    
    # Header backdrop
    content = content.replace("rgba(30, 30, 30, 0.9)", "rgba(255, 255, 255, 0.9)")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Process style.css
replace_in_file('static/css/style.css')

# Process html templates
for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            replace_in_file(os.path.join(root, file))

print("Theme refactored successfully.")
