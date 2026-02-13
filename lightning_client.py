import requests
import json
import os
import codecs
from config import Config

class LightningClient:
    def __init__(self):
        self.config = Config()
        self.base_url = f"https://{self.config.LND_HOST}:{self.config.LND_REST_PORT}"
        self.headers = self._get_headers()
        
        # Disable SSL warnings for self-signed cert in development
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def _get_headers(self):
        """Read macaroon and create headers"""
        try:
            macaroon_path = os.path.expanduser(self.config.LND_MACAROON_PATH)
            with open(macaroon_path, 'rb') as f:
                macaroon_bytes = f.read()
                macaroon = codecs.encode(macaroon_bytes, 'hex').decode('ascii')
            
            return {
                'Grpc-Metadata-macaroon': macaroon
            }
        except FileNotFoundError:
            print(f"Warning: Macaroon not found at {self.config.LND_MACAROON_PATH}")
            print("Make sure Polar is running and paths are correct in config.py")
            return {}
    
    def create_invoice(self, amount_sats, memo, expiry=3600):
        """Generate a Lightning invoice using REST API"""
        url = f"{self.base_url}/v1/invoices"
        
        data = {
            "value": str(amount_sats),
            "memo": memo,
            "expiry": str(expiry)
        }
        
        try:
            response = requests.post(
                url, 
                json=data, 
                headers=self.headers,
                verify=False,  # Skip SSL verification for local dev
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create invoice: {response.text}")
            
            result = response.json()
            
            return {
                'payment_request': result['payment_request'],
                'payment_hash': result['r_hash'],
                'expires_at': expiry
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error connecting to Lightning node: {e}")
    
    def check_invoice(self, payment_hash):
        """Check if an invoice has been paid using REST API"""
        url = f"{self.base_url}/v1/invoice/{payment_hash}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=False,
                timeout=10
            )
            
            if response.status_code != 200:
                return False
            
            result = response.json()
            return result.get('state') == 'SETTLED'
        except requests.exceptions.RequestException:
            return False
    
    def get_node_info(self):
        """Get Lightning node information"""
        url = f"{self.base_url}/v1/getinfo"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=False,
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get node info: {response.text}")
            
            result = response.json()
            
            return {
                'pubkey': result.get('identity_pubkey'),
                'alias': result.get('alias'),
                'num_channels': result.get('num_active_channels'),
                'synced': result.get('synced_to_chain')
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error connecting to Lightning node: {e}")