from app import app, db, User
import bcrypt
from sqlalchemy import text


with app.app_context():
    print("Connected to:", app.config['SQLALCHEMY_DATABASE_URI'])


with app.app_context():
    result = db.session.execute(text("SELECT current_schema();"))
    print("Current schema:", result.scalar())

with app.app_context():
    result = db.session.execute(text("SELECT * FROM information_schema.columns WHERE table_name='users';"))
    for row in result:
        print(row)

with app.app_context():
    result = db.session.execute(text("SELECT schemaname, tablename FROM pg_tables WHERE tablename = 'users';"))
    for row in result:
        print(row)

with app.app_context():
    hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(username="manualtest2", password_hash=hashed_password, role="user")
    db.session.add(new_user)
    db.session.commit()
    print("User added successfully!")

    # Verify
    users = User.query.all()
    for user in users:
        print(user.username, user.role)
