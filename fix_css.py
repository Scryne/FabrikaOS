import glob
import re
import sys

files = glob.glob('app/templates/satin_alma/*.html')
count = 0
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    content = re.sub(r'\s*bg-dark\s*', ' ', content)
    content = re.sub(r'\s*text-light\s*', ' ', content)
    content = re.sub(r'\s*border-secondary\s*', ' ', content)
    content = re.sub(r'\s*border-primary\s*', ' ', content)
    
    content = re.sub(r'class=\"\s+', 'class=\"', content)
    content = re.sub(r'\s+\"', '\"', content)
    content = re.sub(r'class=\"\"', '', content)
    
    content = re.sub(r'\s*table-dark\s*', ' ', content)

    if content != original:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1

print(f"Processed {count} files")
