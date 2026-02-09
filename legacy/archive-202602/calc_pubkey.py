
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
import base64

# Private Key from Inbound 6 DB dump
private_key_b64 = "OH4DmENx2OOx1yiko19zSAnrdl_vz281n_0vGUcFQHk"

try:
    # Decode URL-safe base64 (add padding if needed)
    missing_padding = len(private_key_b64) % 4
    if missing_padding:
        private_key_b64 += '=' * (4 - missing_padding)
        
    private_bytes = base64.urlsafe_b64decode(private_key_b64)
    
    # Load private key
    private_key = x25519.X25519PrivateKey.from_private_bytes(private_bytes)
    
    # Derive public key
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')
    
    print(f"Private Key: {private_key_b64}")
    print(f"Public Key:  {public_key_b64}")
    
except Exception as e:
    print(f"Error: {e}")
