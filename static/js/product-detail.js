/**
 * Product Detail Page JavaScript
 * Handles quantity controls, image gallery, and tabs
 */

class ProductDetail {
    constructor(config) {
        this.pricePerUnit = config.pricePerUnit;
        this.maxStock = config.maxStock;
        
        this.initializeElements();
        this.attachEventListeners();
    }

    initializeElements() {
        // Quantity controls
        this.qtyInput = document.getElementById('quantityInput');
        this.decreaseBtn = document.getElementById('decreaseQty');
        this.increaseBtn = document.getElementById('increaseQty');
        this.totalPriceEl = document.getElementById('totalPrice');
        this.checkoutBtn = document.getElementById('checkoutBtn');

        // Image gallery
        this.mainImage = document.getElementById('mainImage');
        this.thumbnails = document.querySelectorAll('.thumbnail');

        // Tabs
        this.tabButtons = document.querySelectorAll('.tab-btn');
        this.tabPanels = document.querySelectorAll('.tab-panel');

        // Icon buttons
        this.iconButtons = document.querySelectorAll('.icon-btn');
    }

    attachEventListeners() {
        // Quantity controls
        if (this.decreaseBtn) {
            this.decreaseBtn.addEventListener('click', () => this.decreaseQuantity());
        }
        if (this.increaseBtn) {
            this.increaseBtn.addEventListener('click', () => this.increaseQuantity());
        }
        if (this.qtyInput) {
            this.qtyInput.addEventListener('change', () => this.validateQuantity());
        }

        // Image gallery
        this.thumbnails.forEach(thumb => {
            thumb.addEventListener('click', (e) => this.changeImage(e.currentTarget));
        });

        // Tabs
        this.tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.currentTarget));
        });

        // Icon buttons (wishlist/share)
        this.iconButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleIconClick(e.currentTarget));
        });

        // Add to Cart button
        const addToCartBtn = document.getElementById('addToCartBtn');
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', () => {
                const qty = parseInt(this.qtyInput?.value) || 1;
                Cart.addItem({
                    id: addToCartBtn.dataset.id,
                    name: addToCartBtn.dataset.name,
                    price_sats: parseInt(addToCartBtn.dataset.price),
                    image: addToCartBtn.dataset.image,
                    quantity: qty
                });
            });
        }

        // Smooth scroll on page load
        window.addEventListener('load', () => this.handlePageLoad());
    }

    // Quantity Methods
    decreaseQuantity() {
        const currentQty = parseInt(this.qtyInput.value);
        if (currentQty > 1) {
            this.qtyInput.value = currentQty - 1;
            this.updateTotal();
        }
    }

    increaseQuantity() {
        const currentQty = parseInt(this.qtyInput.value);
        if (currentQty < this.maxStock) {
            this.qtyInput.value = currentQty + 1;
            this.updateTotal();
        }
    }

    validateQuantity() {
        let qty = parseInt(this.qtyInput.value);
        if (isNaN(qty) || qty < 1) {
            this.qtyInput.value = 1;
        } else if (qty > this.maxStock) {
            this.qtyInput.value = this.maxStock;
        }
        this.updateTotal();
    }

    updateTotal() {
        const qty = parseInt(this.qtyInput.value) || 1;
        const total = qty * this.pricePerUnit;
        
        // Update display
        if (this.totalPriceEl) {
            this.totalPriceEl.textContent = total.toLocaleString() + ' sats';
        }

        // Update checkout URL
        if (this.checkoutBtn) {
            const url = new URL(this.checkoutBtn.href);
            url.searchParams.set('quantity', qty);
            this.checkoutBtn.href = url.toString();
        }
    }

    // Image Gallery Methods
    changeImage(thumbnail) {
        const newImageSrc = thumbnail.dataset.image;
        if (this.mainImage && newImageSrc) {
            this.mainImage.src = newImageSrc;
            
            // Update active state
            this.thumbnails.forEach(t => t.classList.remove('active'));
            thumbnail.classList.add('active');
        }
    }

    // Tabs Methods
    switchTab(button) {
        const tabId = button.dataset.tab;
        
        // Remove active from all
        this.tabButtons.forEach(b => b.classList.remove('active'));
        this.tabPanels.forEach(p => p.classList.remove('active'));
        
        // Add active to selected
        button.classList.add('active');
        const selectedPanel = document.getElementById(tabId);
        if (selectedPanel) {
            selectedPanel.classList.add('active');
        }
    }

    // Icon Button Methods
    handleIconClick(button) {
        const icon = button.querySelector('span');
        if (icon && icon.textContent === '❤️') {
            // Wishlist animation
            icon.textContent = '💖';
            setTimeout(() => {
                icon.textContent = '❤️';
            }, 1000);
        }
    }

    // Page Load Methods
    handlePageLoad() {
        // Handle hash navigation
        if (window.location.hash) {
            const element = document.querySelector(window.location.hash);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        }
    }
}