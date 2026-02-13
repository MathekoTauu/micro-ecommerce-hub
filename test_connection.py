import os
import grpc
import codecs

# Your configuration
LND_HOST = '127.0.0.1'
LND_PORT = 10001  # Adjust if needed
CERT_PATH = r'C:\Users\tauma\.polar\networks\5\volumes\lnd\alice\tls.cert'
MACAROON_PATH = r'C:\Users\tauma\.polar\networks\5\volumes\lnd\alice\data\chain\bitcoin\regtest\admin.macaroon'

# Check files exist
print("Checking files...")
print(f"TLS Cert exists: {os.path.exists(CERT_PATH)}")
print(f"Macaroon exists: {os.path.exists(MACAROON_PATH)}")

if not os.path.exists(CERT_PATH):
    print(f"\n❌ TLS Cert not found at: {CERT_PATH}")
    print("Please check your network number and node name in Polar.")
    exit(1)

if not os.path.exists(MACAROON_PATH):
    print(f"\n❌ Macaroon not found at: {MACAROON_PATH}")
    print("Please check your network number and node name in Polar.")
    exit(1)

print("\n✅ All files found!")

try:
    # Read files
    with open(MACAROON_PATH, 'rb') as f:
        macaroon_bytes = f.read()
        macaroon = codecs.encode(macaroon_bytes, 'hex')
    
    with open(CERT_PATH, 'rb') as f:
        cert = f.read()
    
    print(f"Certificate size: {len(cert)} bytes")
    print(f"Macaroon size: {len(macaroon_bytes)} bytes")
    
    # Create credentials
    ssl_creds = grpc.ssl_channel_credentials(cert)
    auth_creds = grpc.metadata_call_credentials(
        lambda context, callback: callback([('macaroon', macaroon)], None)
    )
    combined_creds = grpc.composite_channel_credentials(ssl_creds, auth_creds)
    
    # Test connection
    channel = grpc.secure_channel(f'{LND_HOST}:{LND_PORT}', combined_creds)
    
    print(f"\n✅ Successfully connected to LND at {LND_HOST}:{LND_PORT}")
    
except Exception as e:
    print(f"\n❌ Connection error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Polar network is running (green play button)")
    print("2. Verify the port number (check Polar UI)")
    print("3. Try restarting the Polar network")