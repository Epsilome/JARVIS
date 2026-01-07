import os

env_path = ".env"

try:
    # Read as binary to detect encoding issues
    with open(env_path, 'rb') as f:
        raw = f.read()

    print(f"Original size: {len(raw)} bytes")
    
    content = ""
    # Try decoding as utf-16 if BOM is present or it looks like utf-16
    if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
        print("Detected UTF-16 BOM. Decoding...")
        content = raw.decode('utf-16')
    else:
        # Try utf-8 first
        try:
            content = raw.decode('utf-8')
        except UnicodeDecodeError:
            print("UTF-8 decode failed. Trying cp1252...")
            content = raw.decode('cp1252')

    # Now clean the content
    lines = content.splitlines()
    clean_lines = []
    print(f"Read {len(lines)} lines.")
    
    for line in lines:
        line = line.strip()
        if not line: continue
        # Remove null bytes if any crept in
        line = line.replace('\x00', '')
        if '=' in line:
            clean_lines.append(line)
    
    # Write back as clean UTF-8
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(clean_lines) + '\n')
        
    print("Successfully cleaned .env and saved as UTF-8.")
    
    # Verify by printing specific key (safely)
    for l in clean_lines:
        if "TAVILY" in l:
            print(f"Found Key: {l}")

except Exception as e:
    print(f"Error repairing .env: {e}")
