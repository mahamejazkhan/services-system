from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, date
from flask import template_rendered
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-super-secret-key-2024-wopla-admin'  # SECRET KEY ADDED HERE
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://@localhost\\SQLEXPRESS/WoplaDB"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({
        'success': False,
        'message': 'Please login first'
    }), 401


# Database Models (Same as before)
class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    UserID = db.Column(db.Integer, primary_key=True)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(256), nullable=False)
    FirstName = db.Column(db.String(50), nullable=False)
    LastName = db.Column(db.String(50), nullable=False)
    Role = db.Column(db.String(50), nullable=False)
    CompanyID = db.Column(db.Integer)
    IsActive = db.Column(db.Boolean, default=True)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_id(self):
        return str(self.UserID)
    
    @property
    def full_name(self):
        return f"{self.FirstName} {self.LastName}"

class Company(db.Model):
    __tablename__ = 'Companies'
    CompanyID = db.Column(db.Integer, primary_key=True)
    CompanyName = db.Column(db.String(200), unique=True, nullable=False)
    CompanyEmail = db.Column(db.String(120), unique=True, nullable=False)
    Status = db.Column(db.String(20), default='Active')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

class Vendor(db.Model):
    __tablename__ = 'Vendors'
    VendorID = db.Column(db.Integer, primary_key=True)
    VendorName = db.Column(db.String(200), unique=True, nullable=False)
    ContactEmail = db.Column(db.String(120), nullable=False)
    Status = db.Column(db.String(20), default='Active')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

class Dish(db.Model):
    __tablename__ = 'Dishes'
    DishID = db.Column(db.Integer, primary_key=True)
    DishName = db.Column(db.String(200), nullable=False)
    VendorID = db.Column(db.Integer, db.ForeignKey('Vendors.VendorID'), nullable=False)
    CompanyID = db.Column(db.Integer)
    Price = db.Column(db.Numeric(10, 2), nullable=False)
    IsActive = db.Column(db.Boolean, default=True)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'Orders'
    OrderID = db.Column(db.Integer, primary_key=True)
    CompanyID = db.Column(db.Integer, db.ForeignKey('Companies.CompanyID'), nullable=False)
    EmployeeID = db.Column(db.Integer)
    DishID = db.Column(db.Integer, db.ForeignKey('Dishes.DishID'), nullable=False)
    OrderDate = db.Column(db.Date, nullable=False)
    Notes = db.Column(db.String(500))
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

class KioskCounter(db.Model):
    __tablename__ = 'KioskCounters'
    CounterID = db.Column(db.Integer, primary_key=True)
    DishID = db.Column(db.Integer, db.ForeignKey('Dishes.DishID'), nullable=False)
    CounterDate = db.Column(db.Date, nullable=False)
    BaseCount = db.Column(db.Integer, default=0)
    AdditionalCount = db.Column(db.Integer, default=0)
    LastUpdated = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request format'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400
        
        # ========== FIX 1: Super Admin Check ==========
        if email == 'admin@wopla.com' and password == 'Admin@123':
            # Check if user exists
            user = User.query.filter_by(Email=email).first()
            
            # If user doesn't exist, CREATE IT FIRST
            if not user:
                user = User(
                    Email=email,
                    PasswordHash=password,
                    FirstName='Super',
                    LastName='Admin',
                    Role='super_admin',
                    IsActive=True
                )
                db.session.add(user)
                db.session.commit()
                print("✅ Super admin user created successfully")
            
            # NOW login the user
            login_user(user)
            print(f"✅ User logged in: {user.Email}, Role: {user.Role}")
            return jsonify({'success': True, 'redirect': '/super-admin'})
        
        # ========== FIX 2: Check other users ==========
        user = User.query.filter_by(Email=email, IsActive=True).first()
        
        if user and user.PasswordHash == password:
            login_user(user)
            
            if user.Role == 'super_admin':
                redirect_url = '/super-admin'
            elif user.Role == 'client_admin':
                redirect_url = '/client-admin'
            else:
                redirect_url = '/lunch-kiosk'
            
            return jsonify({'success': True, 'redirect': redirect_url})
        
        return jsonify({'success': False, 'message': 'Invalid email or password'})
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/super-admin')
@login_required
def super_admin_dashboard():
    if current_user.Role != 'super_admin':
        return redirect(url_for('login'))
    
    companies = Company.query.all()
    vendors = Vendor.query.all()
    dishes = Dish.query.filter_by(IsActive=True).all()
    orders = Order.query.order_by(Order.CreatedAt.desc()).limit(10).all()
    
    return render_template('super_admin.html', 
                         companies=companies,
                         vendors=vendors,
                         dishes=dishes,
                         orders=orders)
@app.route('/payment-module')
@login_required
def payment_module():
    # sirf super admin ko allow
    if current_user.Role != 'super_admin':
        return redirect(url_for('login'))

    return render_template('payment_module.html')

@app.route('/vendor-admin')
@login_required
def vendor_admin_dashboard():
    # Sirf super admin ya vendor admin allow
    if current_user.Role not in ['super_admin', 'vendor_admin']:
        return redirect(url_for('login'))

    return render_template('vendor_admin.html')


@app.route('/client-admin')
@login_required
def client_admin_dashboard():
    # Allow both super_admin and client_admin roles to access
    if current_user.Role not in ['super_admin', 'client_admin']:
        return redirect(url_for('login'))
    
    # If user is client_admin, show only their company
    if current_user.Role == 'client_admin':
        company = Company.query.get(current_user.CompanyID)
        if not company:
            return redirect(url_for('login'))
        # Note: Make sure your HTML file is named correctly
        # If it's client-admin.html (with hyphen), use that:
        return render_template('client-admin.html', company=company)
    else:
        # Super admin sees all companies
        companies = Company.query.all()
        # Note: Make sure your HTML file is named correctly
        return render_template('client-admin.html', companies=companies)

@app.route('/lunch-kiosk')
@login_required
def lunch_kiosk():
    dishes = Dish.query.filter_by(IsActive=True).all()
    return render_template('lunch_kiosk.html', dishes=dishes)

# API Routes
@app.route('/api/companies', methods=['GET', 'POST'])
@login_required
def handle_companies():
    if current_user.Role != 'super_admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        companies = Company.query.all()
        result = []
        for company in companies:
            result.append({
                'id': company.CompanyID,
                'name': company.CompanyName,
                'email': company.CompanyEmail,
                'status': company.Status
            })
        return jsonify({'companies': result})
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data.get('name') or not data.get('email'):
            return jsonify({'error': 'Name and email required'}), 400
        
        existing = Company.query.filter_by(CompanyName=data['name']).first()
        if existing:
            return jsonify({'error': 'Company already exists'}), 400
        
        company = Company(
            CompanyName=data['name'],
            CompanyEmail=data['email']
        )
        
        try:
            db.session.add(company)
            db.session.commit()
            return jsonify({'success': True, 'company': {
                'id': company.CompanyID,
                'name': company.CompanyName,
                'email': company.CompanyEmail
            }})
        except:
            db.session.rollback()
            return jsonify({'error': 'Database error'}), 500

@app.route('/api/vendors', methods=['GET', 'POST'])
@login_required
def handle_vendors():
    if current_user.Role != 'super_admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        vendors = Vendor.query.all()
        result = []
        for vendor in vendors:
            result.append({
                'id': vendor.VendorID,
                'name': vendor.VendorName,
                'email': vendor.ContactEmail,
                'status': vendor.Status
            })
        return jsonify({'vendors': result})
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data.get('name') or not data.get('email'):
            return jsonify({'error': 'Name and email required'}), 400
        
        vendor = Vendor(
            VendorName=data['name'],
            ContactEmail=data['email']
        )
        
        try:
            db.session.add(vendor)
            db.session.commit()
            return jsonify({'success': True, 'vendor': {
                'id': vendor.VendorID,
                'name': vendor.VendorName,
                'email': vendor.ContactEmail
            }})
        except:
            db.session.rollback()
            return jsonify({'error': 'Database error'}), 500

@app.route('/api/dishes', methods=['GET', 'POST'])
@login_required
def handle_dishes():
    if current_user.Role != 'super_admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        dishes = Dish.query.filter_by(IsActive=True).all()
        result = []
        for dish in dishes:
            vendor = Vendor.query.get(dish.VendorID)
            company = Company.query.get(dish.CompanyID) if dish.CompanyID else None
            result.append({
                'id': dish.DishID,
                'name': dish.DishName,
                'vendor': vendor.VendorName if vendor else 'Unknown',
                'company': company.CompanyName if company else 'All Companies',
                'price': float(dish.Price)
            })
        return jsonify({'dishes': result})
    
    elif request.method == 'POST':
        data = request.get_json()
        dish = Dish(
            DishName=data['name'],
            VendorID=data['vendor_id'],
            CompanyID=data.get('company_id'),
            Price=data['price']
        )
        
        try:
            db.session.add(dish)
            db.session.commit()
            return jsonify({'success': True})
        except:
            db.session.rollback()
            return jsonify({'error': 'Database error'}), 500

@app.route('/api/orders', methods=['GET', 'POST'])
@login_required
def handle_orders():
    if request.method == 'GET':
        if current_user.Role == 'super_admin':
            orders = Order.query.order_by(Order.OrderDate.desc()).all()
        else:
            orders = Order.query.filter_by(CompanyID=current_user.CompanyID)\
                .order_by(Order.OrderDate.desc()).all()
        
        result = []
        for order in orders:
            company = Company.query.get(order.CompanyID)
            dish = Dish.query.get(order.DishID)
            vendor = Vendor.query.get(dish.VendorID) if dish else None
            employee = User.query.get(order.EmployeeID) if order.EmployeeID else None
            
            result.append({
                'id': order.OrderID,
                'company': company.CompanyName if company else 'Unknown',
                'employee': employee.full_name if employee else 'Unknown',
                'dish': dish.DishName if dish else 'Unknown',
                'vendor': vendor.VendorName if vendor else 'Unknown',
                'date': order.OrderDate.strftime('%Y-%m-%d'),
                'notes': order.Notes
            })
        return jsonify({'orders': result})
    
    elif request.method == 'POST':
        data = request.get_json()
        order = Order(
            CompanyID=data['company_id'],
            EmployeeID=data.get('employee_id'),
            DishID=data['dish_id'],
            OrderDate=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            Notes=data.get('notes')
        )
        
        try:
            db.session.add(order)
            db.session.commit()
            return jsonify({'success': True})
        except:
            db.session.rollback()
            return jsonify({'error': 'Database error'}), 500

@app.route('/api/kiosk/counters', methods=['GET', 'POST'])
@login_required
def handle_kiosk_counters():
    if request.method == 'GET':
        today = date.today()
        counters = KioskCounter.query.filter_by(CounterDate=today).all()
        
        result = []
        for counter in counters:
            dish = Dish.query.get(counter.DishID)
            result.append({
                'dish_id': counter.DishID,
                'dish_name': dish.DishName if dish else 'Unknown',
                'base_count': counter.BaseCount,
                'additional_count': counter.AdditionalCount,
                'total_count': counter.BaseCount + counter.AdditionalCount
            })
        return jsonify({'counters': result})
    
    elif request.method == 'POST':
        data = request.get_json()
        today = date.today()
        
        counter = KioskCounter.query.filter_by(
            DishID=data['dish_id'],
            CounterDate=today
        ).first()
        
        if not counter:
            counter = KioskCounter(
                DishID=data['dish_id'],
                CounterDate=today,
                BaseCount=0,
                AdditionalCount=0
            )
            db.session.add(counter)
        
        counter.AdditionalCount += data['change']
        if counter.AdditionalCount < 0:
            counter.AdditionalCount = 0
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except:
            db.session.rollback()
            return jsonify({'error': 'Database error'}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    if current_user.Role == 'super_admin':
        total_companies = Company.query.count()
        total_admins = User.query.filter_by(Role='client_admin').count()
        total_vendors = Vendor.query.count()
        today = date.today()
        todays_orders = Order.query.filter_by(OrderDate=today).count()
        
        return jsonify({
            'total_companies': total_companies,
            'total_admins': total_admins,
            'todays_orders': todays_orders,
            'total_vendors': total_vendors
        })
    else:
        return jsonify({'error': 'Unauthorized'}), 403

# Initialize database
with app.app_context():
    db.create_all()
    
    # Create super admin if not exists
    if not User.query.filter_by(Email='admin@wopla.com').first():
        admin = User(
            Email='admin@wopla.com',
            PasswordHash='Admin@123',
            FirstName='Super',
            LastName='Admin',
            Role='super_admin',
            IsActive=True
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)