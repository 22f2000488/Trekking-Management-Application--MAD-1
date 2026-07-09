from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, Trek, Booking

app = Flask(__name__)
app.config["SECRET_KEY"] = "trekking-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------- HOME AND AUTHENTICATION ----------------

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        full_name = request.form["full_name"].strip()
        phone = request.form["phone"].strip()
        role = request.form["role"]

        if role not in ["user", "staff"]:
            flash("Invalid role.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        status = "pending" if role == "staff" else "active"

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

        if role == "staff":
            flash("Registration successful. Wait for Admin approval.", "success")
        else:
            flash("Registration successful. You can login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        if current_user.role == "staff":
            return redirect(url_for("staff_dashboard"))
        return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        if user.status == "blacklisted":
            flash("Your account has been blacklisted.", "danger")
            return redirect(url_for("login"))

        if user.role == "staff" and user.status == "pending":
            flash("Your Staff account is waiting for Admin approval.", "warning")
            return redirect(url_for("login"))

        login_user(user)

        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        if user.role == "staff":
            return redirect(url_for("staff_dashboard"))
        return redirect(url_for("user_dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("login"))

    return render_template(
        "admin/admin_dashboard.html",
        total_treks=Trek.query.count(),
        total_users=User.query.filter_by(role="user").count(),
        total_staff=User.query.filter_by(role="staff").count(),
        total_bookings=Booking.query.count()
    )


# ---------------- ADMIN TREK MANAGEMENT ----------------

@app.route("/admin/treks")
@login_required
def admin_treks():
    if current_user.role != "admin":
        return redirect(url_for("login"))

    treks = Trek.query.all()
    return render_template("admin/admin_treks.html", treks=treks)


@app.route("/admin/treks/create", methods=["GET", "POST"])
@login_required
def create_trek():
    if current_user.role != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
        total_slots = int(request.form["total_slots"])

        if total_slots <= 0:
            flash("Slots must be greater than zero.", "danger")
            return redirect(url_for("create_trek"))

        if end_date < start_date:
            flash("End date cannot be before start date.", "danger")
            return redirect(url_for("create_trek"))

        trek = Trek(
            name=request.form["name"].strip(),
            location=request.form["location"].strip(),
            difficulty=request.form["difficulty"],
            duration_days=int(request.form["duration_days"]),
            total_slots=total_slots,
            available_slots=total_slots,
            status=request.form["status"],
            start_date=start_date,
            end_date=end_date,
            description=request.form["description"].strip(),
            price=float(request.form["price"] or 0),
            altitude=request.form["altitude"].strip()
        )

        db.session.add(trek)
        db.session.commit()
        flash("Trek created successfully.", "success")
        return redirect(url_for("admin_treks"))

    return render_template("admin/create_trek.html")


@app.route("/admin/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@login_required
def edit_trek(trek_id):
    if current_user.role != "admin":
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":
        total_slots = int(request.form["total_slots"])
        available_slots = int(request.form["available_slots"])
        start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()

        if total_slots <= 0 or available_slots < 0 or available_slots > total_slots:
            flash("Invalid slot values.", "danger")
            return redirect(url_for("edit_trek", trek_id=trek.id))

        if end_date < start_date:
            flash("End date cannot be before start date.", "danger")
            return redirect(url_for("edit_trek", trek_id=trek.id))

        trek.name = request.form["name"].strip()
        trek.location = request.form["location"].strip()
        trek.difficulty = request.form["difficulty"]
        trek.duration_days = int(request.form["duration_days"])
        trek.total_slots = total_slots
        trek.available_slots = available_slots
        trek.status = request.form["status"]
        trek.start_date = start_date
        trek.end_date = end_date
        trek.description = request.form["description"].strip()
        trek.price = float(request.form["price"] or 0)
        trek.altitude = request.form["altitude"].strip()

        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for("admin_treks"))

    return render_template("admin/edit_trek.html", trek=trek)


@app.route("/admin/treks/<int:trek_id>/delete", methods=["POST"])
@login_required
def delete_trek(trek_id):
    if current_user.role != "admin":
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)

    if trek.bookings:
        flash("Cannot delete a trek with booking history.", "danger")
    else:
        db.session.delete(trek)
        db.session.commit()
        flash("Trek deleted successfully.", "success")

    return redirect(url_for("admin_treks"))


@app.route("/admin/treks/<int:trek_id>/assign-staff", methods=["GET", "POST"])
@login_required
def assign_staff(trek_id):
    if current_user.role != "admin":
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)
    active_staff = User.query.filter_by(role="staff", status="active").all()

    if request.method == "POST":
        staff_id = request.form.get("staff_id")

        if staff_id:
            staff = User.query.get_or_404(int(staff_id))

            if staff.role != "staff" or staff.status != "active":
                flash("Only active Staff can be assigned.", "danger")
                return redirect(url_for("assign_staff", trek_id=trek.id))

            trek.assigned_staff_id = staff.id
            flash("Staff assigned successfully.", "success")
        else:
            trek.assigned_staff_id = None
            flash("Staff assignment removed.", "success")

        db.session.commit()
        return redirect(url_for("admin_treks"))

    return render_template("admin/assign_staff.html", trek=trek, active_staff=active_staff)


# ---------------- ADMIN STAFF MANAGEMENT ----------------

@app.route("/admin/staff")
@login_required
def admin_staff():
    if current_user.role != "admin":
        return redirect(url_for("login"))

    staff_members = User.query.filter_by(role="staff").all()
    return render_template("admin/admin_staff.html", staff_members=staff_members)


@app.route("/admin/staff/<int:staff_id>/approve", methods=["POST"])
@login_required
def approve_staff(staff_id):
    if current_user.role != "admin":
        return redirect(url_for("login"))

    staff = User.query.get_or_404(staff_id)

    if staff.role == "staff" and staff.status == "pending":
        staff.status = "active"
        db.session.commit()
        flash("Staff approved.", "success")

    return redirect(url_for("admin_staff"))


@app.route("/admin/staff/<int:staff_id>/blacklist", methods=["POST"])
@login_required
def blacklist_staff(staff_id):
    if current_user.role != "admin":
        return redirect(url_for("login"))

    staff = User.query.get_or_404(staff_id)

    if staff.role == "staff":
        staff.status = "blacklisted"
        db.session.commit()
        flash("Staff blacklisted.", "warning")

    return redirect(url_for("admin_staff"))


@app.route("/admin/staff/<int:staff_id>/activate", methods=["POST"])
@login_required
def activate_staff(staff_id):
    if current_user.role != "admin":
        return redirect(url_for("login"))

    staff = User.query.get_or_404(staff_id)

    if staff.role == "staff":
        staff.status = "active"
        db.session.commit()
        flash("Staff activated.", "success")

    return redirect(url_for("admin_staff"))


# ---------------- ADMIN USER MANAGEMENT ----------------

@app.route("/admin/users")
@login_required
def admin_users():
    if current_user.role != "admin":
        return redirect(url_for("login"))

    users = User.query.filter_by(role="user").all()
    return render_template("admin/admin_users.html", users=users)


@app.route("/admin/users/<int:user_id>/blacklist", methods=["POST"])
@login_required
def blacklist_user(user_id):
    if current_user.role != "admin":
        return redirect(url_for("login"))

    user = User.query.get_or_404(user_id)

    if user.role == "user":
        user.status = "blacklisted"
        db.session.commit()
        flash("User blacklisted.", "warning")

    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/activate", methods=["POST"])
@login_required
def activate_user(user_id):
    if current_user.role != "admin":
        return redirect(url_for("login"))

    user = User.query.get_or_404(user_id)

    if user.role == "user":
        user.status = "active"
        db.session.commit()
        flash("User activated.", "success")

    return redirect(url_for("admin_users"))


# ---------------- ADMIN BOOKINGS AND SEARCH ----------------

@app.route("/admin/bookings")
@login_required
def admin_bookings():
    if current_user.role != "admin":
        return redirect(url_for("login"))

    bookings = Booking.query.all()
    return render_template("admin/admin_bookings.html", bookings=bookings)


@app.route("/admin/search")
@login_required
def admin_search():
    if current_user.role != "admin":
        return redirect(url_for("login"))

    query_text = request.args.get("q", "").strip()
    search_type = request.args.get("type", "treks")
    results = []

    if query_text:
        if search_type == "treks":
            items = Trek.query.all()
        elif search_type == "staff":
            items = User.query.filter_by(role="staff").all()
        else:
            items = User.query.filter_by(role="user").all()

        for item in items:
            if search_type == "treks":
                name = item.name
            else:
                name = item.full_name

            name_match = query_text.lower() in name.lower()
            id_match = query_text.isdigit() and item.id == int(query_text)

            if name_match or id_match:
                results.append(item)

    return render_template(
        "admin/admin_search.html",
        results=results,
        query_text=query_text,
        search_type=search_type
    )


# ---------------- STAFF ----------------

@app.route("/staff/dashboard")
@login_required
def staff_dashboard():
    if current_user.role != "staff":
        return redirect(url_for("login"))

    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=current_user.id
    ).all()

    return render_template("staff/staff_dashboard.html", assigned_treks=assigned_treks)


@app.route("/staff/trek/<int:trek_id>/manage", methods=["GET", "POST"])
@login_required
def staff_manage_trek(trek_id):
    if current_user.role != "staff":
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("staff_dashboard"))

    if request.method == "POST":
        slots = int(request.form["available_slots"])
        status = request.form["status"]

        if slots < 0 or slots > trek.total_slots:
            flash("Invalid available slots.", "danger")
            return redirect(url_for("staff_manage_trek", trek_id=trek.id))

        if status not in ["Open", "Closed", "Completed"]:
            flash("Invalid status.", "danger")
            return redirect(url_for("staff_manage_trek", trek_id=trek.id))

        trek.available_slots = slots
        trek.status = status

        if status == "Completed":
            for booking in trek.bookings:
                if booking.status == "Booked":
                    booking.status = "Completed"

        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for("staff_dashboard"))

    return render_template("staff/staff_manage_trek.html", trek=trek)


@app.route("/staff/trek/<int:trek_id>/participants")
@login_required
def trek_participants(trek_id):
    if current_user.role != "staff":
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("staff_dashboard"))

    bookings = Booking.query.filter_by(trek_id=trek.id).all()

    return render_template(
        "staff/trek_participants.html",
        trek=trek,
        bookings=bookings
    )


# ---------------- USER ----------------

@app.route("/user/dashboard")
@login_required
def user_dashboard():
    if current_user.role != "user":
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip().lower()
    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "").strip().lower()

    treks = Trek.query.filter_by(status="Open").all()
    available_treks = []

    for trek in treks:
        name_ok = not search or search in trek.name.lower()
        difficulty_ok = not difficulty or trek.difficulty == difficulty
        location_ok = not location or location in trek.location.lower()

        if name_ok and difficulty_ok and location_ok:
            available_treks.append(trek)

    active_bookings = Booking.query.filter_by(
        user_id=current_user.id,
        status="Booked"
    ).all()

    return render_template(
        "user/user_dashboard.html",
        available_treks=available_treks,
        active_bookings=active_bookings,
        search=search,
        difficulty=difficulty,
        location=location
    )


@app.route("/trek/<int:trek_id>")
@login_required
def trek_details(trek_id):
    if current_user.role != "user":
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)
    return render_template("user/trek_details.html", trek=trek)


@app.route("/trek/<int:trek_id>/book", methods=["POST"])
@login_required
def book_trek(trek_id):
    if current_user.role != "user":
        return redirect(url_for("login"))

    trek = Trek.query.get_or_404(trek_id)

    if trek.status != "Open":
        flash("This trek is not open for booking.", "danger")
        return redirect(url_for("user_dashboard"))

    if trek.available_slots <= 0:
        flash("No slots are available.", "danger")
        return redirect(url_for("user_dashboard"))

    old_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek.id,
        status="Booked"
    ).first()

    if old_booking:
        flash("You have already booked this trek.", "warning")
        return redirect(url_for("user_dashboard"))

    booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        status="Booked"
    )

    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()

    flash("Trek booked successfully.", "success")
    return redirect(url_for("user_dashboard"))


@app.route("/user/bookings")
@login_required
def my_bookings():
    if current_user.role != "user":
        return redirect(url_for("login"))

    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template("user/my_bookings.html", bookings=bookings)


@app.route("/user/booking/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    if current_user.role != "user":
        return redirect(url_for("login"))

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        flash("You cannot cancel this booking.", "danger")
        return redirect(url_for("my_bookings"))

    if booking.status != "Booked":
        flash("This booking cannot be cancelled.", "warning")
        return redirect(url_for("my_bookings"))

    booking.status = "Cancelled"
    booking.trek.available_slots += 1
    db.session.commit()

    flash("Booking cancelled.", "success")
    return redirect(url_for("my_bookings"))


@app.route("/user/history")
@login_required
def trekking_history():
    if current_user.role != "user":
        return redirect(url_for("login"))

    completed_bookings = Booking.query.filter_by(
        user_id=current_user.id,
        status="Completed"
    ).all()

    return render_template(
        "user/trekking_history.html",
        completed_bookings=completed_bookings
    )


@app.route("/user/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if current_user.role != "user":
        return redirect(url_for("login"))

    if request.method == "POST":
        full_name = request.form["full_name"].strip()

        if not full_name:
            flash("Full name is required.", "danger")
            return redirect(url_for("edit_profile"))

        current_user.full_name = full_name
        current_user.phone = request.form["phone"].strip()
        current_user.bio = request.form["bio"].strip()

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("edit_profile"))

    return render_template("user/edit_profile.html")


# ---------------- DATABASE AND DEFAULT ADMIN ----------------

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(role="admin").first()

    if not admin:
        admin = User(
            username="admin",
            email="admin@trek.com",
            password=generate_password_hash("admin123"),
            full_name="System Administrator",
            phone="",
            role="admin",
            status="active"
        )

        db.session.add(admin)
        db.session.commit()
        print("Default Admin created.")


if __name__ == "__main__":
    app.run(debug=True)
