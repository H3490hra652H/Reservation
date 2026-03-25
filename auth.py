from flask_login import LoginManager, UserMixin

# create login manager
login_manager = LoginManager()


# User class
class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role


# dummy users (later bisa dari database)
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "kitchen": {"password": "kitchen123", "role": "kitchen"}
}


@login_manager.user_loader
def load_user(user_id):
    user = users.get(user_id)
    if user:
        return User(user_id, user["role"])
    return None