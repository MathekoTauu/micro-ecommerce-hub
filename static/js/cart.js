/**
 * ZapMarket Shopping Cart
 * Client-side cart using localStorage
 */

const Cart = {
    STORAGE_KEY: 'zapmarket_cart',

    // Get all items from cart
    getItems() {
        try {
            return JSON.parse(localStorage.getItem(this.STORAGE_KEY)) || [];
        } catch {
            return [];
        }
    },

    // Save items to cart
    saveItems(items) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(items));
        this.updateCartCount();
        this.renderCartDrawer();
    },

    // Add item to cart
    addItem(product) {
        const items = this.getItems();
        const existing = items.find(item => item.id === product.id);

        if (existing) {
            existing.quantity += product.quantity || 1;
        } else {
            items.push({
                id: product.id,
                name: product.name,
                price_sats: product.price_sats,
                image: product.image,
                quantity: product.quantity || 1
            });
        }

        this.saveItems(items);
        this.showNotification(`${product.name} added to cart!`);
    },

    // Remove item from cart
    removeItem(productId) {
        const items = this.getItems().filter(item => item.id !== productId);
        this.saveItems(items);
    },

    // Update item quantity
    updateQuantity(productId, quantity) {
        const items = this.getItems();
        const item = items.find(i => i.id === productId);
        if (item) {
            if (quantity <= 0) {
                this.removeItem(productId);
                return;
            }
            item.quantity = quantity;
            this.saveItems(items);
        }
    },

    // Clear entire cart
    clear() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.updateCartCount();
        this.renderCartDrawer();
    },

    // Get total number of items
    getCount() {
        return this.getItems().reduce((sum, item) => sum + item.quantity, 0);
    },

    // Get total price in sats
    getTotal() {
        return this.getItems().reduce((sum, item) => sum + (item.price_sats * item.quantity), 0);
    },

    // Update the cart count badge in navbar
    updateCartCount() {
        const countEl = document.getElementById('cart-count');
        if (countEl) {
            const count = this.getCount();
            countEl.textContent = count;
            countEl.classList.toggle('has-items', count > 0);
        }
    },

    // Show a brief notification
    showNotification(message) {
        // Remove existing notification
        const existing = document.querySelector('.cart-notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = 'cart-notification';
        notification.innerHTML = `<span>🛒</span> ${message}`;
        document.body.appendChild(notification);

        // Trigger animation
        requestAnimationFrame(() => notification.classList.add('show'));

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 2500);
    },

    // Toggle cart drawer open/close
    toggleDrawer() {
        const drawer = document.getElementById('cart-drawer');
        const overlay = document.getElementById('cart-overlay');
        if (drawer && overlay) {
            const isOpen = drawer.classList.contains('open');
            drawer.classList.toggle('open');
            overlay.classList.toggle('open');
            document.body.style.overflow = isOpen ? '' : 'hidden';
        }
    },

    closeDrawer() {
        const drawer = document.getElementById('cart-drawer');
        const overlay = document.getElementById('cart-overlay');
        if (drawer && overlay) {
            drawer.classList.remove('open');
            overlay.classList.remove('open');
            document.body.style.overflow = '';
        }
    },

    // Render the cart drawer contents
    renderCartDrawer() {
        const container = document.getElementById('cart-drawer-items');
        const totalEl = document.getElementById('cart-drawer-total');
        const emptyEl = document.getElementById('cart-drawer-empty');
        const footerEl = document.getElementById('cart-drawer-footer');

        if (!container) return;

        const items = this.getItems();

        if (items.length === 0) {
            container.innerHTML = '';
            if (emptyEl) emptyEl.style.display = 'block';
            if (footerEl) footerEl.style.display = 'none';
            return;
        }

        if (emptyEl) emptyEl.style.display = 'none';
        if (footerEl) footerEl.style.display = 'block';

        container.innerHTML = items.map(item => `
            <div class="cart-drawer-item" data-id="${item.id}">
                <img src="/static/images/products/${item.image}" alt="${item.name}" class="cart-item-img">
                <div class="cart-item-details">
                    <h4>${item.name}</h4>
                    <p class="cart-item-price">${item.price_sats.toLocaleString()} sats</p>
                    <div class="cart-item-qty">
                        <button class="qty-btn" onclick="Cart.updateQuantity('${item.id}', ${item.quantity - 1})">−</button>
                        <span>${item.quantity}</span>
                        <button class="qty-btn" onclick="Cart.updateQuantity('${item.id}', ${item.quantity + 1})">+</button>
                        <button class="cart-remove-btn" onclick="Cart.removeItem('${item.id}')">🗑️</button>
                    </div>
                </div>
            </div>
        `).join('');

        if (totalEl) {
            totalEl.textContent = this.getTotal().toLocaleString() + ' sats';
        }
    },

    // Initialize cart on page load
    init() {
        this.updateCartCount();

        // Cart icon click -> toggle drawer
        const cartIcon = document.getElementById('cart-icon');
        if (cartIcon) {
            cartIcon.addEventListener('click', (e) => {
                e.preventDefault();
                this.renderCartDrawer();
                this.toggleDrawer();
            });
        }

        // Overlay click -> close drawer
        const overlay = document.getElementById('cart-overlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.closeDrawer());
        }

        // Close button
        const closeBtn = document.getElementById('cart-drawer-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeDrawer());
        }

        // Clear cart button
        const clearBtn = document.getElementById('cart-clear-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (confirm('Clear all items from your cart?')) {
                    this.clear();
                }
            });
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => Cart.init());
