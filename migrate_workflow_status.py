from sqlalchemy import create_engine, text

print("Connecting to DB...")

engine = create_engine("sqlite:///./app.db", future=True)

with engine.connect() as conn:
    print("Running ALTER TABLE...")
    conn.execute(text("ALTER TABLE workflows ADD COLUMN status TEXT DEFAULT 'in_progress';"))
    conn.commit()

print("✔ Column 'status' added to workflows table.")
