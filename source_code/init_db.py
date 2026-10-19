import os
from app import app, db, User


def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create default admin user if it doesn't exist
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

if __name__ == '__main__':
    init_db() 