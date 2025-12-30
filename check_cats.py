from app.db.session import SessionLocal
from app.models.product import Category

db = SessionLocal()
try:
    cats = db.query(Category).all()
    print("CATEGORIES_FOUND:", [c.name for c in cats])
except Exception as e:
    print("ERROR:", e)
finally:
    db.close()
