from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from sqlalchemy import text  # Import text function

app = Flask(__name__)

# Database Configuration
DB_NAME = "wakigwe_db"
DB_USER = "devlisa"
DB_PASSWORD = "Devnjeri03$" 
DB_HOST = "localhost"
DB_PORT = "3307"  

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Test database connection
try:
    with app.app_context():
        db.session.execute(text("SELECT 1"))  # Use text() to execute raw SQL
    print("✅ Database connection successful!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
