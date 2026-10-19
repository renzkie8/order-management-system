# Order Management System

A Flask-based order management system with user authentication and role-based access control.

## Features

- User Authentication (Admin and Customer roles)
- Product Management (**Admin only**)
- Customer Management (**Admin only**)
- Order Management
- Dashboard for both Admin and Customers
- Responsive UI with Bootstrap
- **Product Deletion** (Admin can now delete products)
- **Customer Profile Editing** (Customers can now edit their own profile from the dashboard)
- **Customer Deletion and Editing** (Admins can now edit and delete customers)

## Setup Instructions

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure MySQL is running and create the database:
```sql
CREATE DATABASE cccs105;
```

3. Initialize the database with default admin user:
```bash
venv\Scripts\activate

python init_db.py
```
4. Set environment variable for Flask:

(venv) app.py -- can skip this part if app.py can be read 


5. Run the application:
```bash
flask run
```

6. Access the application at http://123.0.0.1:5000/localhost:5000

## Default Admin Credentials

- Username: admin
- Password: admin123

## youtube_video_link:
- https://youtu.be/TemlVesiu04 

## User Roles

### Admin
- Full access to all features
- Can manage products and customers
- Can view all orders
- Access to admin dashboard

### Customer
- Can view and create orders
- Can view their own order history
- Access to customer dashboard

## Security Notes

- Change the default admin password after first login
- The SECRET_KEY in app.py should be changed in production
- Database credentials should be stored in environment variables in production

## Database Schema
- Products: product_id, name, description, price, stock_quantity
- Customers: customer_id, name, email, phone, address
- Orders: order_id, customer_id, order_date, total_amount, status
- Order_Items: order_item_id, order_id, product_id, quantity, price 