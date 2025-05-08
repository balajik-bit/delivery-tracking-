from sqlalchemy import text
from extensions import db

def upgrade():
    with db.engine.connect() as conn:
        # Add featured column to products table
        conn.execute(text("""
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS featured BOOLEAN DEFAULT FALSE
        """))
        
        # Set some products as featured
        conn.execute(text("""
            UPDATE products 
            SET featured = TRUE 
            WHERE id IN (1, 2, 3)
        """))
        conn.commit()

def downgrade():
    with db.engine.connect() as conn:
        # Remove featured column
        conn.execute(text("""
            ALTER TABLE products
            DROP COLUMN IF EXISTS featured
        """))
        conn.commit() 