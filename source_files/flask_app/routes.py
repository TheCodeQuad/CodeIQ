from app import app

@app.route("/users")
def list_users():
    # Dummy data for now
    return {"users": ["Alice", "Bob", "Charlie"]}
