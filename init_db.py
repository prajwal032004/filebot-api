import os
from app import app, db

def init_database():
    """Initialize the database and create all tables"""
    with app.app_context():
        # Create database tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Create upload directory
        upload_dir = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            print(f"✓ Upload directory created: {upload_dir}")
        else:
            print(f"✓ Upload directory already exists: {upload_dir}")
        
        print("\n" + "="*50)
        print("Database initialization completed!")
        print("="*50)
        print("\nYou can now run the application with:")
        print("  python app.py")

if __name__ == '__main__':
    init_database()