from extensions import db
from flask import current_app
from sqlalchemy import text

def upgrade():
    with current_app.app_context():
        # Add new columns
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS featured BOOLEAN DEFAULT FALSE'))
            conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS weight FLOAT'))
            conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS length FLOAT'))
            conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS width FLOAT'))
            conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS height FLOAT'))
            conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
            conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
            conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(50)'))
            
            # Rename image_url to image if it exists
            conn.execute(text('ALTER TABLE products CHANGE COLUMN IF EXISTS image_url image VARCHAR(200)'))
            
            # Change price column type from NUMERIC to FLOAT
            conn.execute(text('ALTER TABLE products MODIFY COLUMN price FLOAT NOT NULL'))
            conn.commit()

def downgrade():
    with current_app.app_context():
        with db.engine.connect() as conn:
            # Remove new columns
            conn.execute(text('ALTER TABLE products DROP COLUMN IF EXISTS featured'))
            conn.execute(text('ALTER TABLE products DROP COLUMN IF EXISTS weight'))
            conn.execute(text('ALTER TABLE products DROP COLUMN IF EXISTS length'))
            conn.execute(text('ALTER TABLE products DROP COLUMN IF EXISTS width'))
            conn.execute(text('ALTER TABLE products DROP COLUMN IF EXISTS height'))
            conn.execute(text('ALTER TABLE products DROP COLUMN IF EXISTS created_at'))
            conn.execute(text('ALTER TABLE products DROP COLUMN IF EXISTS updated_at'))
            conn.execute(text('ALTER TABLE products DROP COLUMN IF EXISTS category'))
            
            # Rename image back to image_url
            conn.execute(text('ALTER TABLE products CHANGE COLUMN IF EXISTS image image_url VARCHAR(255)'))
            
            # Change price column type back to NUMERIC
            conn.execute(text('ALTER TABLE products MODIFY COLUMN price NUMERIC(10,2) NOT NULL'))
            conn.commit() 