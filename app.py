from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, User


app = Flask(__name__)


app.config["SECRET_KEY"] = "TMA-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


with app.app_context():

    db.create_all()

    admin = User.query.filter_by(role="admin").first()

    if not admin:

        admin = User(username="admin",
            email="admin@trek.com",
            password=generate_password_hash("admin123"),
            full_name="System Administrator",
            phone="",
            role="admin",
            status="active")

        db.session.add(admin)
        db.session.commit()
        print("Created Admin")


@app.route("/")
def home():

    return "Trekking Management Application"


if __name__ == "__main__":

    app.run(debug=True)