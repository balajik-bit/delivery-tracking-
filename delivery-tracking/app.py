from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import jwt
from functools import wraps
from config import Config
from extensions import db, login_manager
from models.user import User
from models.customer import Customer
from models.product import Product
from models.order import Order
from models.order_item import OrderItem
from models.delivery import Delivery, DeliveryStatusUpdate
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add this after the app initialization
@app.template_filter('status_color')
def status_color(status):
    colors = {
        'pending': 'warning',
        'packing': 'info',
        'shipping': 'primary',
        'out_for_delivery': 'info',
        'delivered': 'success'
    }
    return colors.get(status, 'secondary')

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/products')
def products():
    # Get featured products
    featured_products = Product.query.filter_by(featured=True).limit(3).all()
    
    # Get all products
    products = Product.query.all()
    
    return render_template('products.html', 
                         featured_products=featured_products,
                         products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    # Get related products from the same category
    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'true'
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if is_admin and user.is_admin:
                login_user(user)
                flash('Welcome Admin!', 'success')
                return redirect(url_for('admin_dashboard'))
            elif not is_admin and not user.is_admin:
                login_user(user)
                flash('Welcome back!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid login credentials', 'danger')
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        role = request.form.get('role', 'customer')  # Default to customer if not specified
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))
        
        try:
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role
            )
            db.session.add(user)
            db.session.commit()
            
            # Create customer profile only for customer role
            if role == 'customer':
                customer = Customer(
                    user_id=user.id,
                    full_name=username,
                    phone=phone,
                    address=address
                )
                db.session.add(customer)
                db.session.commit()
            
            # Log in the user
            login_user(user)
            flash('Account created successfully!', 'success')
            
            # Redirect based on role
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration', 'danger')
            return redirect(url_for('signup'))
            
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'customer':
        orders = Order.query.filter_by(customer_id=current_user.customer.id).order_by(Order.order_date.desc()).all()
        return render_template('dashboard.html', orders=orders)
    else:
        # Get statistics for admin/staff dashboard
        total_orders = Order.query.count()
        active_deliveries = Delivery.query.filter(Delivery.status != 'delivered').count()
        total_customers = Customer.query.count()
        
        # Get recent activity (last 10 orders)
        recent_activity = Order.query.order_by(Order.order_date.desc()).limit(10).all()
        
        return render_template('admin.html',
                             total_orders=total_orders,
                             active_deliveries=active_deliveries,
                             total_customers=total_customers,
                             recent_activity=recent_activity)

@app.route('/track')
@login_required
def track_delivery_form():
    tracking_number = request.args.get('tracking_number')
    if not tracking_number:
        return render_template('tracking.html')

    # Find delivery by tracking number
    delivery = Delivery.query.filter_by(tracking_number=tracking_number).first()
    if not delivery:
        flash('Invalid tracking number', 'warning')
        return render_template('tracking.html')

    # Get status updates
    status_updates = DeliveryStatusUpdate.query.filter_by(
        delivery_id=delivery.id
    ).order_by(DeliveryStatusUpdate.timestamp.desc()).all()

    return render_template('tracking.html', 
                         delivery=delivery, 
                         status_updates=status_updates)

@app.route('/track/<tracking_number>')
@login_required
def track_delivery(tracking_number):
    delivery = Delivery.query.filter_by(tracking_number=tracking_number).first_or_404()
    
    # Get status updates
    status_updates = DeliveryStatusUpdate.query.filter_by(
        delivery_id=delivery.id
    ).order_by(DeliveryStatusUpdate.timestamp.desc()).all()
    
    return render_template('tracking.html', 
                         delivery=delivery, 
                         status_updates=status_updates)

@app.route('/test-db')
def test_db():
    try:
        # Try to query the database
        db.session.execute('SELECT 1')
        return jsonify({'status': 'success', 'message': 'Database connection successful!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/order', methods=['POST'])
@login_required
def place_order():
    # Get form data
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    # Get product
    product = Product.query.get(product_id)
    if not product:
        flash('Invalid product selected', 'error')
        return redirect(request.referrer or url_for('products'))
    
    # Validate quantity
    if quantity <= 0:
        flash('Invalid quantity selected', 'error')
        return redirect(request.referrer or url_for('products'))
    
    if quantity > product.stock:
        flash(f'Not enough stock for {product.name}', 'error')
        return redirect(request.referrer or url_for('products'))
    
    try:
        # Calculate total
        total = product.price * quantity
        
        # Create order
        order = Order(
            customer_id=current_user.customer.id,
            total=total,
            status='pending',
            shipping_address=current_user.customer.address,
            shipping_phone=current_user.customer.phone,
            shipping_name=current_user.username
        )
        db.session.add(order)
        db.session.commit()

        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=product.price
        )
        db.session.add(order_item)
        
        # Update product stock
        product.stock -= quantity
        db.session.commit()

        # Create delivery
        tracking_number = str(uuid.uuid4())[:8].upper()
        delivery = Delivery(
            order_id=order.id,
            tracking_number=tracking_number,
            status='pending',
            current_location='Processing Center',
            estimated_delivery=datetime.now() + timedelta(days=5)
        )
        db.session.add(delivery)
        db.session.commit()

        # Create initial status update
        status_update = DeliveryStatusUpdate(
            delivery_id=delivery.id,
            status='pending',
            description='Order received and processing started',
            location='Processing Center'
        )
        db.session.add(status_update)
        db.session.commit()

        flash('Order placed successfully! You can track your delivery using the tracking number: ' + tracking_number)
        return redirect(request.referrer or url_for('products'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while processing your order. Please try again.', 'error')
        return redirect(request.referrer or url_for('products'))

@app.route('/update-delivery/<int:delivery_id>', methods=['POST'])
@login_required
def update_delivery(delivery_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    delivery = Delivery.query.get_or_404(delivery_id)
    status = request.form.get('status')
    location = request.form.get('location')
    description = request.form.get('description')

    delivery.status = status
    delivery.current_location = location

    status_update = DeliveryStatusUpdate(
        delivery_id=delivery.id,
        status=status,
        description=description,
        location=location
    )
    db.session.add(status_update)

    if status == 'delivered':
        delivery.actual_delivery = datetime.now()

    db.session.commit()
    return jsonify({'success': True})

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update user profile
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        current_user.customer.full_name = request.form.get('full_name')
        current_user.customer.phone = request.form.get('phone')
        current_user.customer.address = request.form.get('address')
        
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template('settings.html')

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect')
        return redirect(url_for('settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match')
        return redirect(url_for('settings'))
    
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Password changed successfully!')
    return redirect(url_for('settings'))

@app.route('/update-notifications', methods=['POST'])
@login_required
def update_notifications():
    email_notifications = request.form.get('email_notifications') == 'on'
    sms_notifications = request.form.get('sms_notifications') == 'on'
    
    # Update notification preferences in the database
    current_user.customer.email_notifications = email_notifications
    current_user.customer.sms_notifications = sms_notifications
    db.session.commit()
    
    flash('Notification settings updated successfully!')
    return redirect(url_for('settings'))

@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password')
    
    if not check_password_hash(current_user.password_hash, password):
        flash('Incorrect password')
        return redirect(url_for('settings'))
    
    # Delete the user and associated data
    db.session.delete(current_user)
    db.session.commit()
    
    logout_user()
    flash('Your account has been deleted')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    orders = Order.query.all()
    return render_template('admin.html', orders=orders)

@app.route('/admin/orders/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'success': False, 'error': 'Status is required'}), 400
    
    valid_statuses = ['pending', 'packing', 'shipping', 'out_for_delivery', 'delivered']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    try:
        # Update order status
        order.status = new_status
        
        # Create delivery status update if delivery exists
        if order.delivery:
            status_update = DeliveryStatusUpdate(
                delivery_id=order.delivery.id,
                status=new_status,
                description=f'Order status updated to {new_status}',
                location=order.shipping_address
            )
            db.session.add(status_update)
            
            # Update delivery status
            order.delivery.status = new_status
            if new_status == 'delivered':
                order.delivery.actual_delivery = datetime.now()
        
        db.session.commit()
        flash('Order status updated successfully', 'success')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/orders/<int:order_id>/details')
@login_required
def order_details(order_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    order = Order.query.get_or_404(order_id)
    
    # Render order details template
    html = render_template('_order_details.html', order=order)
    return jsonify({'html': html})

# Product Management Routes
@app.route('/admin/products/<int:product_id>')
@login_required
def get_product(product_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': float(product.price),
        'stock': product.stock,
        'category': product.category,
        'image': product.image
    })

@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/products/add', methods=['POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        category = request.form.get('category')
        
        # Handle image upload
        image = request.files.get('image')
        image_path = None
        if image and image.filename:
            filename = secure_filename(image.filename)
            image_path = f'/static/images/products/{filename}'
            image.save(os.path.join('static/images/products', filename))
        
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category,
            image=image_path
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({'success': True, 'product_id': product.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/admin/products/update', methods=['POST'])
@login_required
def update_product():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        product_id = request.form.get('product_id')
        product = Product.query.get_or_404(product_id)
        
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.category = request.form.get('category')
        
        # Handle image upload
        image = request.files.get('image')
        if image and image.filename:
            filename = secure_filename(image.filename)
            image_path = f'/static/images/products/{filename}'
            image.save(os.path.join('static/images/products', filename))
            product.image = image_path
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/create-test-order')
def create_test_order():
    try:
        # Create a test customer if none exists
        customer = Customer.query.first()
        if not customer:
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('password'),
                role='customer'
            )
            db.session.add(user)
            db.session.commit()
            
            customer = Customer(
                user_id=user.id,
                full_name='Test User',
                address='123 Test St',
                phone='1234567890'
            )
            db.session.add(customer)
            db.session.commit()
        
        # Create a test order
        order = Order(
            customer_id=customer.id,
            total=99.99,
            status='pending',
            shipping_address='123 Test St',
            shipping_phone='1234567890',
            shipping_name='Test User'
        )
        db.session.add(order)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Test order created', 'order_id': order.id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


