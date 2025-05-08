from extensions import db
from flask import current_app
from sqlalchemy import text

def upgrade():
    with current_app.app_context():
        with db.engine.connect() as conn:
            # Create orders table if it doesn't exist
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
            
            # Update users table
            conn.execute(text('ALTER TABLE users MODIFY COLUMN role VARCHAR(20) DEFAULT "customer"'))
            
            # Update customers table
            conn.execute(text('ALTER TABLE customers MODIFY COLUMN address TEXT'))
            
            # Create order_items table if it doesn't exist
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
            conn.commit()

def downgrade():
    with current_app.app_context():
        with db.engine.connect() as conn:
            # Drop order_items table
            conn.execute(text('DROP TABLE IF EXISTS order_items'))
            
            # Drop orders table
            conn.execute(text('DROP TABLE IF EXISTS orders'))
            
            # Revert users table
            conn.execute(text('ALTER TABLE users MODIFY COLUMN role ENUM("customer", "admin", "delivery_agent") NOT NULL'))
            
            # Revert customers table
            conn.execute(text('ALTER TABLE customers MODIFY COLUMN address TEXT NOT NULL'))
            conn.commit() 