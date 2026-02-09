
import os

PEM_FILE = "/root/certs_keep/ssl/haproxy.pem"
OUT_DIR = "/root/portal_bot/certs"

def extract_certs():
    if not os.path.exists(PEM_FILE):
        print(f"Error: {PEM_FILE} not found")
        return

    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        print(f"Created {OUT_DIR}")

    with open(PEM_FILE, 'r') as f:
        content = f.read()

    # Split by END tag
    # Usually: Cert -> Chain -> Key OR Key -> Cert -> Chain
    # We need to identify blocks
    
    certs = []
    keys = []
    
    current_block = []
    in_block = False
    
    for line in content.splitlines():
        if "BEGIN" in line:
            in_block = True
            current_block = [line]
        elif "END" in line:
            current_block.append(line)
            in_block = False
            block_content = "\n".join(current_block)
            if "PRIVATE KEY" in line:
                keys.append(block_content)
            elif "CERTIFICATE" in line:
                certs.append(block_content)
        elif in_block:
            current_block.append(line)

    if not keys:
        print("Error: No private key found in haproxy.pem")
        return
    
    if not certs:
        print("Error: No certificates found in haproxy.pem")
        return

    # Write key
    key_path = os.path.join(OUT_DIR, "privkey.pem")
    with open(key_path, 'w') as f:
        f.write(keys[0] + "\n")
    print(f"Saved key to {key_path}")

    # Write fullchain (All certs)
    cert_path = os.path.join(OUT_DIR, "fullchain.pem")
    with open(cert_path, 'w') as f:
        for cert in certs:
            f.write(cert + "\n")
    print(f"Saved fullchain to {cert_path}")

if __name__ == "__main__":
    extract_certs()
