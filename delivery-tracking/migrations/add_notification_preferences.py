from sqlalchemy import text
from extensions import db

def upgrade():
    with db.engine.connect() as conn:
        # Add notification preference columns
        conn.execute(text("""
            ALTER TABLE customers
            ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS sms_notifications BOOLEAN DEFAULT FALSE
        """))
        conn.commit()

def downgrade():
    with db.engine.connect() as conn:
        # Remove notification preference columns
        conn.execute(text("""
            ALTER TABLE customers
            DROP COLUMN IF EXISTS email_notifications,
            DROP COLUMN IF EXISTS sms_notifications
        """))
        conn.commit() 