from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (LoginManager, login_user, logout_user, login_required, current_user)
from werkzeug.security import generate_password_hash
from models import db, User


app = Flask(__name__)


app.config["SECRET_KEY"] = "TMA-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(User, int(user_id))


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
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        phone = request.form["phone"]
        role = request.form["role"]


        if role not in ["user", "staff"]:

            flash("Invalid role.", "danger")

            return redirect(url_for("register"))


        # Check username

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:

            flash("Username already exists.", "danger")

            return redirect(url_for("register"))


        # Check email

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:

            flash("Email already registered.", "danger")

            return redirect(url_for("register"))


        # Staff needs Admin approval

        if role == "staff":

            status = "pending"

        else:

            status = "active"


        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            full_name=full_name,
            phone=phone,
            role=role,
            status=status
        )


        db.session.add(user)

        db.session.commit()


        flash("Registration successful.", "success")

        return redirect(url_for("login"))


    return render_template("register.html")


# Login

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]


        user = User.query.filter_by(
            email=email
        ).first()


        if not user:

            flash("Invalid email or password.", "danger")

            return redirect(url_for("login"))


        if not check_password_hash(
            user.password,
            password
        ):

            flash("Invalid email or password.", "danger")

            return redirect(url_for("login"))


        if user.status == "blacklisted":

            flash("Your account is blacklisted.", "danger")

            return redirect(url_for("login"))


        if user.role == "staff" and user.status == "pending":

            flash(
                "Wait for Admin approval.",
                "warning"
            )

            return redirect(url_for("login"))


        login_user(user)


        if user.role == "admin":

            return redirect(
                url_for("admin_dashboard")
            )


        elif user.role == "staff":

            return redirect(
                url_for("staff_dashboard")
            )


        else:

            return redirect(
                url_for("user_dashboard")
            )


    return render_template("login.html")


# Logout

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


# Basic Admin Dashboard

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():

    if current_user.role != "admin":

        return "Access Denied", 403


    return "Admin Dashboard"


# Basic Staff Dashboard

@app.route("/staff/dashboard")
@login_required
def staff_dashboard():

    if current_user.role != "staff":

        return "Access Denied", 403


    return "Staff Dashboard"


# Basic User Dashboard

@app.route("/user/dashboard")
@login_required
def user_dashboard():

    if current_user.role != "user":

        return "Access Denied", 403


    return "User Dashboard"

if __name__ == "__main__":

    app.run(debug=True)