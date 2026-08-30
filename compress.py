import os
import sys
import subprocess

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

# Try to import modules, install if necessary
def import_or_install(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        return __import__(import_name)
    except ImportError:
        print(f"Installing {package}...")
        if install_package(package):
            try:
                return __import__(import_name)
            except ImportError:
                pass
        print(f"Failed to install {package}")
        return None

htmlmin = import_or_install('htmlmin', 'htmlmin')
csscompressor = import_or_install('csscompressor', 'csscompressor')
jsmin = import_or_install('jsmin', 'jsmin')

if not htmlmin:
    print("Warning: htmlmin not available, skipping HTML compression")
if not csscompressor:
    print("Warning: csscompressor not available, skipping CSS compression")
if not jsmin:
    print("Warning: jsmin not available, skipping JS compression")

def compress_html(filepath):
    if not htmlmin:
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    try:
        compressed = htmlmin.minify(content, 
                                   remove_empty_space=True,
                                   remove_all_empty_space=True, 
                                   reduce_boolean_attributes=True,
                                   remove_optional_attribute_quotes=True,
                                   reduce_empty_attributes=True,
                                   keep_html_and_head_opening_tags=True,
                                   keep_closing_slash=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(compressed)
        print(f"Compressed HTML: {filepath}")
    except Exception as e:
        print(f"Error compressing {filepath}: {e}")

def compress_css(filepath):
    if not csscompressor:
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    try:
        compressed = csscompressor.compress(content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(compressed)
        print(f"Compressed CSS: {filepath}")
    except Exception as e:
        print(f"Error compressing {filepath}: {e}")

def compress_js(filepath):
    if not jsmin:
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    try:
        compressed = jsmin.jsmin(content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(compressed)
        print(f"Compressed JS: {filepath}")
    except Exception as e:
        print(f"Error compressing {filepath}: {e}")

def main():
    base_dir = '.'
    # Exclude .git directory
    exclude_dirs = {'.git', '__pycache__', 'node_modules'}
    
    for root, dirs, files in os.walk(base_dir):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.html'):
                compress_html(filepath)
            elif file.endswith('.css'):
                compress_css(filepath)
            elif file.endswith('.js'):
                # Skip search-index.json? It's .json, not .js
                if file != 'search-index.json':
                    compress_js(filepath)

if __name__ == '__main__':
    main()
