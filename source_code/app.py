from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename


# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/product_images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
migrate = Migrate(app, db)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='customer')  # 'admin' or 'customer'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Database Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(255))  # Store the image filename

    order_items = db.relationship(
        'OrderItem',
        backref='product',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user = db.relationship('User', backref=db.backref('customer', uselist=False))

    orders = db.relationship(
        'Order',
        backref='customer',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')

    items = db.relationship(
        'OrderItem',
        backref='order',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, role='customer')  # Always set role as customer
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Ensure customer profile is created and not duplicated
        customer = Customer.query.filter_by(user_id=user.id).first()
        if not customer:
            customer = Customer(name=username, email=email, phone=phone, address=address, user_id=user.id)
            db.session.add(customer)
            db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# Dashboard routes
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('customer_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    total_products = Product.query.count()
    total_customers = Customer.query.count()
    total_orders = Order.query.count()
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_customers=total_customers,
                         total_orders=total_orders,
                         recent_orders=recent_orders)

# Helper function to get cart from session
def get_cart():
    return session.get('cart', {})

def save_cart(cart):
    session['cart'] = cart

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    if current_user.role != 'customer':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    if product.stock_quantity < quantity:
        flash('Not enough stock available!', 'danger')
        return redirect(url_for('customer_dashboard'))
    cart = get_cart()
    cart_item = cart.get(str(product_id), {'quantity': 0, 'name': product.name, 'price': product.price, 'image_filename': product.image_filename})
    cart_item['quantity'] += quantity
    cart[str(product_id)] = cart_item
    save_cart(cart)
    flash(f'Added {quantity} x {product.name} to cart!', 'success')
    return redirect(url_for('customer_dashboard'))

@app.route('/cart')
@login_required
def view_cart():
    if current_user.role != 'customer':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    cart = get_cart()
    products = []
    total = 0
    for pid, item in cart.items():
        subtotal = item['quantity'] * item['price']
        products.append({**item, 'id': int(pid), 'subtotal': subtotal})
        total += subtotal
    return render_template('cart.html', products=products, total=total)

@app.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    if current_user.role != 'customer':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    cart = get_cart()
    if str(product_id) in cart:
        quantity = int(request.form.get('quantity', 1))
        if quantity <= 0:
            cart.pop(str(product_id))
        else:
            cart[str(product_id)]['quantity'] = quantity
        save_cart(cart)
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    if current_user.role != 'customer':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    cart = get_cart()
    if not cart:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('view_cart'))
    customer = Customer.query.filter_by(user_id=current_user.id).first()
    if not customer:
        flash('Customer profile not found!', 'danger')
        return redirect(url_for('dashboard'))
    total_amount = sum(item['quantity'] * item['price'] for item in cart.values())
    order = Order(customer_id=customer.id, total_amount=total_amount)
    db.session.add(order)
    db.session.commit()
    for pid, item in cart.items():
        product = Product.query.get(int(pid))
        if product.stock_quantity < item['quantity']:
            flash(f'Not enough stock for {product.name}!', 'danger')
            db.session.delete(order)
            db.session.commit()
            return redirect(url_for('view_cart'))
        order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=item['quantity'], price=product.price)
        db.session.add(order_item)
        product.stock_quantity -= item['quantity']
    db.session.commit()
    session['cart'] = {}
    flash('Order placed successfully!', 'success')
    return redirect(url_for('orders'))

# Update customer dashboard to show available products
@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    customer = Customer.query.filter_by(user_id=current_user.id).first()
    if not customer:
        customer = Customer(name=current_user.username, email=current_user.email, user_id=current_user.id)
        db.session.add(customer)
        db.session.commit()
    orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.order_date.desc()).all()
    products = Product.query.filter(Product.stock_quantity > 0).all()
    return render_template('customer/dashboard.html', customer=customer, orders=orders, products=products)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
@login_required
def products():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/customers')
@login_required
def customers():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))

    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        customer.address = request.form['address']
        db.session.commit()
        flash('Customer updated successfully!')
        return redirect(url_for('customers'))

    return render_template('edit_customer.html', customer=customer)


@app.route('/customers/delete/<int:customer_id>')
@login_required
def delete_customer(customer_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))

    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully!')
    return redirect(url_for('customers'))

@app.route('/add_customer', methods=['GET', 'POST'])
@login_required
def add_customer():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        
        customer = Customer(name=name, email=email, phone=phone, address=address)
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully!')
        return redirect(url_for('customers'))
    
    return render_template('add_customer.html')


@app.route('/orders')
@login_required
def orders():
    if current_user.role == 'admin':
        orders = Order.query.all()
    else:
        customer = Customer.query.filter_by(user_id=current_user.id).first()
        orders = Order.query.filter_by(customer_id=customer.id).all()
    return render_template('orders.html', orders=orders)

@app.route('/order/<int:order_id>')
@login_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.role != 'admin' and order.customer.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('order_details.html', order=order)

@app.route('/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.role != 'admin' and order.customer.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if order.status == 'cancelled':
        flash('Order is already cancelled!')
        return redirect(url_for('orders'))
    
    # Return items to stock
    for item in order.items:
        product = Product.query.get(item.product_id)
        product.stock_quantity += item.quantity
    
    order.status = 'cancelled'
    db.session.commit()
    
    flash('Order cancelled successfully!')
    return redirect(url_for('orders'))

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock_quantity = int(request.form['stock_quantity'])
        
        # Check if image was uploaded
        if 'image' not in request.files:
            flash('No image file selected', 'danger')
            return redirect(request.url)
        
        image = request.files['image']
        if image.filename == '':
            flash('No image selected', 'danger')
            return redirect(request.url)
        
        if not allowed_file(image.filename):
            flash('Invalid file type. Allowed types: png, jpg, jpeg, gif', 'danger')
            return redirect(request.url)
        
        # Save the image
        filename = secure_filename(image.filename)
        # Add timestamp to filename to make it unique
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        product = Product(
            name=name,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            image_filename=filename
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!')
        return redirect(url_for('products'))
    
    return render_template('add_product.html')

@app.route('/product_image/<filename>')
def product_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



@app.route('/create_order', methods=['GET', 'POST'])
@login_required
def create_order():
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        
        product = Product.query.get_or_404(product_id)
        if product.stock_quantity < quantity:
            flash('Not enough stock available!')
            return redirect(url_for('create_order'))
        
        customer = Customer.query.filter_by(user_id=current_user.id).first()
        if not customer:
            flash('Customer profile not found!')
            return redirect(url_for('dashboard'))
        
        order = Order(customer_id=customer.id, total_amount=product.price * quantity)
        db.session.add(order)
        db.session.commit()
        
        order_item = OrderItem(order_id=order.id, product_id=product_id, 
                             quantity=quantity, price=product.price)
        db.session.add(order_item)
        
        product.stock_quantity -= quantity
        db.session.commit()
        
        flash('Order created successfully!')
        return redirect(url_for('orders'))
    
    products = Product.query.all()
    return render_template('create_order.html', products=products)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock_quantity = int(request.form['stock_quantity'])
        # Handle image update
        image = request.files.get('image')
        if image and image.filename:
            if allowed_file(image.filename):
                # Remove old image if exists
                if product.image_filename:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                filename = secure_filename(image.filename)
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image_filename = filename
            else:
                flash('Invalid file type. Allowed types: png, jpg, jpeg, gif', 'danger')
                return redirect(request.url)
        db.session.commit()
        flash('Product updated successfully!')
        return redirect(url_for('products'))
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    product = Product.query.get_or_404(product_id)
    # Remove image file if exists
    if product.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!')
    return redirect(url_for('products'))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'customer':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    customer = Customer.query.filter_by(user_id=current_user.id).first()
    if not customer:
        flash('Customer profile not found!', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        customer.address = request.form['address']
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('customer_dashboard'))
    return render_template('edit_profile.html', customer=customer)

@app.route('/admin/order/<int:order_id>/prepare', methods=['POST'])
@login_required
def admin_prepare_order(order_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    order = Order.query.get_or_404(order_id)
    if order.status == 'pending':
        order.status = 'preparing'
        db.session.commit()
        flash(f'Order #{order.id} marked as preparing.', 'success')
    else:
        flash('Invalid status transition.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/order/<int:order_id>/deliver', methods=['POST'])
@login_required
def admin_deliver_order(order_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    order = Order.query.get_or_404(order_id)
    if order.status == 'preparing':
        order.status = 'delivering'
        db.session.commit()
        flash(f'Order #{order.id} marked as delivering.', 'success')
    else:
        flash('Invalid status transition.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/order/<int:order_id>/complete', methods=['POST'])
@login_required
def admin_complete_order(order_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    order = Order.query.get_or_404(order_id)
    if order.status == 'delivering':
        order.status = 'completed'
        db.session.commit()
        flash(f'Order #{order.id} marked as completed.', 'success')
    else:
        flash('Invalid status transition.', 'warning')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():

        # Create default admin user if it doesn't exist
        db.create_all()
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password(os.environ['ADMIN_PASSWORD'])  # Default password
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created!")
            print("Username: admin")
            print("Admin password loaded from environment")
    
    app.run(debug=True) 