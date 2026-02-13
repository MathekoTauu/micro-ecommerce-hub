// Checkout flow logic
let currentPaymentHash = null;
let paymentCheckInterval = null;

// Update total when quantity changes
document.getElementById('quantity').addEventListener('input', (e) => {
    const quantity = parseInt(e.target.value) || 1;
    const total = basePrice * quantity;
    document.getElementById('total-sats').textContent = total;
});

// Generate Lightning invoice
document.getElementById('generate-invoice-btn').addEventListener('click', async () => {
    const quantity = parseInt(document.getElementById('quantity').value) || 1;
    
    try {
        // Show loading state
        const btn = document.getElementById('generate-invoice-btn');
        btn.disabled = true;
        btn.textContent = 'Generating Invoice...';
        
        // Call API to create invoice
        const response = await fetch('/api/create-invoice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            btn.disabled = false;
            btn.textContent = 'Generate Lightning Invoice';
            return;
        }
        
        // Store payment hash
        currentPaymentHash = data.payment_hash;
        
        // Display payment panel
        document.getElementById('payment-panel').style.display = 'block';
        document.querySelector('.order-summary').style.display = 'none';
        
        // Generate QR code
        const qrContainer = document.getElementById('qr-code');
        qrContainer.innerHTML = ''; // Clear previous QR
        new QRCode(qrContainer, {
            text: data.payment_request,
            width: 256,
            height: 256
        });
        
        // Display invoice text
        document.getElementById('invoice-text').value = data.payment_request;
        
        // Start checking for payment
        startPaymentCheck(data.payment_hash);
        
    } catch (error) {
        console.error('Error generating invoice:', error);
        alert('Failed to generate invoice. Please try again.\n' + error.message);
        const btn = document.getElementById('generate-invoice-btn');
        btn.disabled = false;
        btn.textContent = 'Generate Lightning Invoice';
    }
});

// Copy invoice to clipboard
document.getElementById('copy-invoice-btn').addEventListener('click', () => {
    const invoiceText = document.getElementById('invoice-text');
    invoiceText.select();
    document.execCommand('copy');
    
    // Show feedback
    const btn = document.getElementById('copy-invoice-btn');
    const originalText = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => {
        btn.textContent = originalText;
    }, 2000);
});

// Check payment status periodically
function startPaymentCheck(paymentHash) {
    paymentCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/check-payment/${paymentHash}`);
            const data = await response.json();
            
            if (data.paid) {
                // Payment received!
                clearInterval(paymentCheckInterval);
                showPaymentSuccess();
            }
        } catch (error) {
            console.error('Error checking payment:', error);
        }
    }, 2000); // Check every 2 seconds
}

// Show payment success
function showPaymentSuccess() {
    document.getElementById('payment-status').style.display = 'none';
    document.getElementById('payment-success').style.display = 'block';
    
    // Redirect to confirmation page after 3 seconds
    setTimeout(() => {
        window.location.href = '/order-confirmation';
    }, 3000);
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (paymentCheckInterval) {
        clearInterval(paymentCheckInterval);
    }
});