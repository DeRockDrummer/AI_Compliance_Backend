# backend/promote_admin.py

from app.db.session import SessionLocal
from app.db.models.user import User

def promote_admin(email: str):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"❌ User not found: {email}")
            return

        user.role = "admin"
        db.add(user)
        db.commit()

        print(f"✅ User promoted to admin: {email}")

    except Exception as e:
        print("❌ Error promoting user:", e)

    finally:
        db.close()


if __name__ == "__main__":
    # ⭐ CHANGE THIS EMAIL to the user you want to promote
    promote_admin("test@example.com")
