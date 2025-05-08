from extensions import db
from flask import current_app
from sqlalchemy import text

def upgrade():
    with current_app.app_context():
        with db.engine.connect() as conn:
            # Create users table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(128) NOT NULL,
                    role VARCHAR(20) DEFAULT 'customer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            
            # Create customers table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    address TEXT,
                    phone VARCHAR(20),
                    email_notifications BOOLEAN DEFAULT TRUE,
                    sms_notifications BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            '''))
            
            # Create products table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS products (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    price FLOAT NOT NULL,
                    stock INT NOT NULL DEFAULT 0,
                    image VARCHAR(200),
                    category VARCHAR(50),
                    featured BOOLEAN DEFAULT FALSE,
                    weight FLOAT,
                    length FLOAT,
                    width FLOAT,
                    height FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            '''))
            
            # Create orders table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    customer_id INT NOT NULL,
                    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total FLOAT NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    shipping_address TEXT,
                    shipping_phone VARCHAR(20),
                    shipping_name VARCHAR(100),
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
                )
            '''))
            
            # Create order_items table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    order_id INT NOT NULL,
                    product_id INT NOT NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    price FLOAT NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            '''))
            
            # Create deliveries table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS deliveries (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    order_id INT NOT NULL,
                    tracking_number VARCHAR(20) UNIQUE NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    current_location VARCHAR(100),
                    estimated_delivery DATETIME,
                    actual_delivery DATETIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                )
            '''))
            
            # Create delivery_status_updates table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS delivery_status_updates (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    delivery_id INT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    description TEXT,
                    location VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (delivery_id) REFERENCES deliveries(id) ON DELETE CASCADE
                )
            '''))
            
            conn.commit()

def downgrade():
    with current_app.app_context():
        with db.engine.connect() as conn:
            # Drop tables in reverse order
            conn.execute(text('DROP TABLE IF EXISTS delivery_status_updates'))
            conn.execute(text('DROP TABLE IF EXISTS deliveries'))
            conn.execute(text('DROP TABLE IF EXISTS order_items'))
            conn.execute(text('DROP TABLE IF EXISTS orders'))
            conn.execute(text('DROP TABLE IF EXISTS products'))
            conn.execute(text('DROP TABLE IF EXISTS customers'))
            conn.execute(text('DROP TABLE IF EXISTS users'))
            conn.commit() 