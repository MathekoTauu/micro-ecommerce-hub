import time
import threading
from lightning_client import LightningClient
import lightning_pb2 as ln

class PaymentDetector:
    def __init__(self, on_payment_callback):
        self.ln_client = LightningClient()
        self.on_payment_callback = on_payment_callback
        self.running = False
    
    def start(self):
        """Start monitoring for incoming payments"""
        self.running = True
        thread = threading.Thread(target=self._monitor_invoices, daemon=True)
        thread.start()
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
    
    def _monitor_invoices(self):
        """Background thread to monitor invoice settlements"""
        request = ln.InvoiceSubscription()
        
        try:
            for invoice in self.ln_client.stub.SubscribeInvoices(request):
                if not self.running:
                    break
                
                if invoice.state == ln.Invoice.SETTLED:
                    # Payment received!
                    payment_data = {
                        'payment_hash': invoice.r_hash.hex(),
                        'amount_sats': invoice.value,
                        'memo': invoice.memo,
                        'settled_at': invoice.settle_date
                    }
                    
                    # Trigger callback (update database, release escrow, etc.)
                    self.on_payment_callback(payment_data)
        
        except Exception as e:
            print(f"Error monitoring invoices: {e}")
            if self.running:
                time.sleep(5)
                self._monitor_invoices()  # Reconnect

# Example callback function
def handle_payment_received(payment_data):
    print(f"Payment received: {payment_data}")
    # Update order status in database
    # Release escrow
    # Send confirmation email
    pass

# Start detector
if __name__ == '__main__':
    detector = PaymentDetector(on_payment_callback=handle_payment_received)
    detector.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detector.stop()