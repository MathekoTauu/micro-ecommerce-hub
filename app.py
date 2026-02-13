from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import json
from datetime import datetime
from lightning_client import LightningClient
from config import Config
from models import User, user_db
import os

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

# Test route for static file serving
@app.route('/test-css')
def test_css():
    return '''<html><head><link rel="stylesheet" href="/static/css/style.css"></head><body><h1>Test CSS</h1><div class="test">If this is styled, static works.</div></body></html>'''

# Initialize extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Make current_user available in templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Initialize Lightning client
try:
    ln_client = LightningClient()
    print("✅ Lightning client initialized")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Lightning client: {e}")
    ln_client = None

# User loader
@login_manager.user_loader
def load_user(user_id):
    return user_db.get_user_by_id(user_id)

# Helper functions
def load_products():
    try:
        with open(app.config['PRODUCTS_FILE'], 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_products(products):
    with open(app.config['PRODUCTS_FILE'], 'w') as f:
        json.dump(products, f, indent=2)

def load_vendors():
    try:
        with open(app.config['VENDORS_FILE'], 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_vendors(vendors):
    with open(app.config['VENDORS_FILE'], 'w') as f:
        json.dump(vendors, f, indent=2)

def load_freelancers():
    try:
        with open('data/freelancers.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_hire_requests():
    try:
        with open('data/hire_requests.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_hire_requests(requests_list):
    with open('data/hire_requests.json', 'w', encoding='utf-8') as f:
        json.dump(requests_list, f, indent=2, ensure_ascii=False)

def load_orders():
    try:
        with open('data/orders.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_order(order_data):
    orders = load_orders()
    orders.append(order_data)
    with open('data/orders.json', 'w') as f:
        json.dump(orders, f, indent=2)

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        role = request.form.get('role', 'vendor')
        
        try:
            user = user_db.create_user(email, password, name, role)
            
            if role == 'vendor':
                vendors = load_vendors()
                vendor_data = {
                    'id': f"vendor_{len(vendors) + 1:03d}",
                    'user_id': user.id,
                    'name': name,
                    'location': '',
                    'rating': 5.0,
                    'total_sales': 0,
                    'joined_date': datetime.utcnow().isoformat(),
                    'description': ''
                }
                vendors.append(vendor_data)
                save_vendors(vendors)
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = user_db.get_user_by_email(email)
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ============================================
# PUBLIC ROUTES
# ============================================

@app.route('/')
def index():
    """Homepage with product listing"""
    products = load_products()
    return render_template('index.html', products=products)

@app.route('/cart')
def cart_page():
    """Full cart page"""
    products = load_products()
    return render_template('cart.html', products=products)

@app.route('/product/<product_id>')
def product_detail(product_id):
    """Product detail page"""
    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
    
    vendors = load_vendors()
    vendor = next((v for v in vendors if v['id'] == product.get('vendor_id')), None)
    
    return render_template('product.html', product=product, vendor=vendor)

@app.route('/checkout/<product_id>')
def checkout(product_id):
    """Checkout page"""
    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
    
    if 'price_sats' not in product or product['price_sats'] is None:
        flash('Invalid product data', 'error')
        return redirect(url_for('index'))
    
    try:
        product['price_sats'] = int(product['price_sats'])
    except (ValueError, TypeError):
        flash('Invalid product price', 'error')
        return redirect(url_for('index'))
    
    return render_template('checkout.html', product=product)

# ============================================
# FREELANCER ROUTES
# ============================================

@app.route('/freelancers')
def freelancers():
    """Freelancer services listing page"""
    freelancer_list = load_freelancers()
    
    # Filter by skill if provided
    skill_filter = request.args.get('skill', '').strip()
    if skill_filter:
        freelancer_list = [
            f for f in freelancer_list
            if skill_filter.lower() in [s.lower() for s in f.get('skills', [])]
        ]
    
    # Filter by availability
    available_only = request.args.get('available', '').strip()
    if available_only == 'true':
        freelancer_list = [f for f in freelancer_list if f.get('available', False)]
    
    # Collect all unique skills for the filter dropdown
    all_freelancers = load_freelancers()
    all_skills = sorted(set(
        skill for f in all_freelancers for skill in f.get('skills', [])
    ))
    
    return render_template('freelancers.html',
                           freelancers=freelancer_list,
                           all_skills=all_skills,
                           current_skill=skill_filter,
                           available_only=available_only)

@app.route('/freelancer/<freelancer_id>')
def freelancer_profile(freelancer_id):
    """Individual freelancer profile page"""
    freelancers_list = load_freelancers()
    freelancer = next((f for f in freelancers_list if f['id'] == freelancer_id), None)
    
    if not freelancer:
        flash('Freelancer not found', 'error')
        return redirect(url_for('freelancers'))
    
    return render_template('freelancer_profile.html', freelancer=freelancer)

@app.route('/freelancer/<freelancer_id>/hire', methods=['POST'])
def hire_freelancer(freelancer_id):
    """Submit a hire request to a freelancer"""
    freelancers_list = load_freelancers()
    freelancer = next((f for f in freelancers_list if f['id'] == freelancer_id), None)
    
    if not freelancer:
        flash('Freelancer not found', 'error')
        return redirect(url_for('freelancers'))
    
    if not freelancer.get('available', False):
        flash('This freelancer is currently unavailable.', 'error')
        return redirect(url_for('freelancer_profile', freelancer_id=freelancer_id))
    
    # Gather form data
    client_name = request.form.get('client_name', '').strip()
    client_email = request.form.get('client_email', '').strip()
    project_title = request.form.get('project_title', '').strip()
    project_description = request.form.get('project_description', '').strip()
    estimated_hours = request.form.get('estimated_hours', '').strip()
    budget_sats = request.form.get('budget_sats', '').strip()
    
    # Validate required fields
    if not all([client_name, client_email, project_title, project_description]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('freelancer_profile', freelancer_id=freelancer_id))
    
    # Create hire request
    hire_requests = load_hire_requests()
    hire_request = {
        'id': f"hire_{len(hire_requests) + 1:04d}",
        'freelancer_id': freelancer_id,
        'freelancer_name': freelancer['name'],
        'client_name': client_name,
        'client_email': client_email,
        'project_title': project_title,
        'project_description': project_description,
        'estimated_hours': int(estimated_hours) if estimated_hours else None,
        'budget_sats': int(budget_sats) if budget_sats else None,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'messages': []
    }
    
    hire_requests.append(hire_request)
    save_hire_requests(hire_requests)
    
    flash(f'Your hire request has been sent to {freelancer["name"]}! They will review it shortly.', 'success')
    return redirect(url_for('freelancer_profile', freelancer_id=freelancer_id))

@app.route('/hire-requests')
def my_hire_requests():
    """View hire requests (filtered by email)"""
    email = request.args.get('email', '').strip()
    
    if not email:
        return render_template('hire_requests.html', hire_requests=[], email='', searched=False)
    
    all_requests = load_hire_requests()
    my_requests = [r for r in all_requests if r.get('client_email', '').lower() == email.lower()]
    # Sort newest first
    my_requests.sort(key=lambda r: r.get('created_at', ''), reverse=True)
    
    return render_template('hire_requests.html', hire_requests=my_requests, email=email, searched=True)

@app.route('/freelancer-dashboard')
def freelancer_dashboard():
    """Dashboard for freelancers to manage incoming hire requests"""
    freelancer_id = request.args.get('freelancer_id', '').strip()
    
    if not freelancer_id:
        # Show freelancer selector
        freelancers_list = load_freelancers()
        return render_template('freelancer_dashboard.html', 
                             freelancers=freelancers_list, 
                             selected_freelancer=None, 
                             hire_requests=[])
    
    freelancers_list = load_freelancers()
    freelancer = next((f for f in freelancers_list if f['id'] == freelancer_id), None)
    
    if not freelancer:
        flash('Freelancer not found', 'error')
        return redirect(url_for('freelancer_dashboard'))
    
    all_requests = load_hire_requests()
    my_requests = [r for r in all_requests if r.get('freelancer_id') == freelancer_id]
    my_requests.sort(key=lambda r: r.get('created_at', ''), reverse=True)
    
    return render_template('freelancer_dashboard.html',
                         freelancers=freelancers_list,
                         selected_freelancer=freelancer,
                         hire_requests=my_requests)

@app.route('/hire-request/<request_id>/update', methods=['POST'])
def update_hire_request(request_id):
    """Update the status of a hire request"""
    new_status = request.form.get('status', '').strip()
    
    if new_status not in ['accepted', 'declined', 'completed']:
        flash('Invalid status.', 'error')
        return redirect(url_for('freelancer_dashboard'))
    
    hire_requests = load_hire_requests()
    hire_req = next((r for r in hire_requests if r['id'] == request_id), None)
    
    if not hire_req:
        flash('Hire request not found.', 'error')
        return redirect(url_for('freelancer_dashboard'))
    
    hire_req['status'] = new_status
    hire_req['updated_at'] = datetime.utcnow().isoformat()
    save_hire_requests(hire_requests)
    
    freelancer_id = hire_req.get('freelancer_id', '')
    flash(f'Request has been {new_status}.', 'success')
    return redirect(url_for('freelancer_dashboard', freelancer_id=freelancer_id))

# ============================================
# VENDOR ROUTES
# ============================================

@app.route('/vendor/dashboard')
@login_required
def vendor_dashboard():
    """Vendor dashboard"""
    if current_user.role != 'vendor':
        flash('Access denied. Vendor account required.', 'error')
        return redirect(url_for('index'))
    
    vendors = load_vendors()
    vendor = next((v for v in vendors if v.get('user_id') == current_user.id), None)
    
    if not vendor:
        flash('Vendor profile not found.', 'error')
        return redirect(url_for('index'))
    
    products = load_products()
    vendor_products = [p for p in products if p.get('vendor_id') == vendor['id']]
    
    orders = load_orders()
    vendor_orders = [o for o in orders if any(p['id'] == o.get('product_id') for p in vendor_products)]
    
    stats = {
        'total_sales': sum(o.get('amount_sats', 0) for o in vendor_orders),
        'total_orders': len(vendor_orders),
        'active_products': len([p for p in vendor_products if p.get('stock', 0) > 0]),
        'total_products': len(vendor_products)
    }
    
    return render_template('vendor_dashboard.html', 
                         vendor=vendor, 
                         products=vendor_products,
                         orders=vendor_orders,
                         stats=stats)

@app.route('/vendor/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new product"""
    if current_user.role != 'vendor':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        vendors = load_vendors()
        vendor = next((v for v in vendors if v.get('user_id') == current_user.id), None)
        
        if not vendor:
            flash('Vendor profile not found.', 'error')
            return redirect(url_for('vendor_dashboard'))
        
        products = load_products()
        
        new_product = {
            'id': f"prod_{len(products) + 1:03d}",
            'vendor_id': vendor['id'],
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price_sats': int(request.form.get('price_sats')),
            'category': request.form.get('category'),
            'stock': int(request.form.get('stock', 0)),
            'location': vendor.get('location', 'Unknown'),
            'image': request.form.get('image', 'placeholder.jpg'),
            'created_at': datetime.utcnow().isoformat()
        }
        
        products.append(new_product)
        save_products(products)
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('vendor_dashboard'))
    
    return render_template('add_product.html')

@app.route('/vendor/products/<product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit product"""
    if current_user.role != 'vendor':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('vendor_dashboard'))
    
    vendors = load_vendors()
    vendor = next((v for v in vendors if v.get('user_id') == current_user.id), None)
    
    if not vendor or product.get('vendor_id') != vendor['id']:
        flash('You do not have permission to edit this product.', 'error')
        return redirect(url_for('vendor_dashboard'))
    
    if request.method == 'POST':
        product['name'] = request.form.get('name')
        product['description'] = request.form.get('description')
        product['price_sats'] = int(request.form.get('price_sats'))
        product['category'] = request.form.get('category')
        product['stock'] = int(request.form.get('stock', 0))
        
        save_products(products)
        flash('Product updated successfully!', 'success')
        return redirect(url_for('vendor_dashboard'))
    
    return render_template('edit_product.html', product=product)

@app.route('/vendor/products/<product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete product"""
    if current_user.role != 'vendor':
        flash('Access denied.', 'error')
        return redirect(url_for('vendor_dashboard'))
    
    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('vendor_dashboard'))
    
    vendors = load_vendors()
    vendor = next((v for v in vendors if v.get('user_id') == current_user.id), None)
    
    if not vendor or product.get('vendor_id') != vendor['id']:
        flash('Permission denied.', 'error')
        return redirect(url_for('vendor_dashboard'))
    
    products = [p for p in products if p['id'] != product_id]
    save_products(products)
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('vendor_dashboard'))

@app.route('/vendor/profile', methods=['GET', 'POST'])
@login_required
def vendor_profile():
    """Vendor profile management"""
    if current_user.role != 'vendor':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    vendors = load_vendors()
    vendor = next((v for v in vendors if v.get('user_id') == current_user.id), None)
    
    if not vendor:
        flash('Vendor profile not found.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        vendor['name'] = request.form.get('name')
        vendor['location'] = request.form.get('location')
        vendor['description'] = request.form.get('description')
        
        save_vendors(vendors)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('vendor_dashboard'))
    
    return render_template('vendor_profile.html', vendor=vendor)

# ============================================
# API ROUTES
# ============================================

@app.route('/api/create-invoice', methods=['POST'])
def create_invoice():
    """Create Lightning invoice"""
    if not ln_client:
        return jsonify({'error': 'Lightning client not available'}), 503
    
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    amount_sats = product['price_sats'] * quantity
    
    try:
        invoice = ln_client.create_invoice(
            amount_sats=amount_sats,
            memo=f"{product['name']} x{quantity}",
            expiry=app.config['PAYMENT_TIMEOUT']
        )
        
        order_data = {
            'product_id': product_id,
            'quantity': quantity,
            'amount_sats': amount_sats,
            'payment_hash': invoice['payment_hash'],
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        save_order(order_data)
        
        return jsonify({
            'payment_request': invoice['payment_request'],
            'payment_hash': invoice['payment_hash'],
            'amount_sats': amount_sats,
            'expires_at': invoice['expires_at']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-payment/<payment_hash>')
def check_payment(payment_hash):
    """Check payment status"""
    if not ln_client:
        return jsonify({'error': 'Lightning client not available'}), 503
    
    try:
        is_paid = ln_client.check_invoice(payment_hash)
        return jsonify({'paid': is_paid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    flash('Page not found', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    flash('An internal error occurred', 'error')
    return redirect(url_for('index'))

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting ZapMarket")
    print("="*60)
    print(f"📍 Running on: http://localhost:5000")
    print(f"⚡ Lightning: {'Connected' if ln_client else 'Not Connected'}")
    print(f"👤 Authentication: Enabled")
    print("="*60)
    print("\nAvailable routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)