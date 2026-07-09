# Trekking Management Application
---
## Project Description

The Trekking Management Application is a web application developed for managing trekking activities.

The application provides separate functionality for three types of users:

1. Admin
2. Trek Staff
3. User (Trekker)

The Admin manages treks, staff members, users and bookings. Trek Staff members manage the treks assigned to them. Users can search and book available treks and view their booking history.

---

## Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite
- Jinja2
- HTML
- CSS
- Bootstrap

---

## Main Features

### Admin

The Admin is created automatically when the application starts for the first time.

Admin can:
-View Dashboard Statistics
-Can add, edit, or remove trek
-Can approve and blacklist trek staff
-Can assign staff to a particular trek
-Can view all the users, staff, and treks
-Can search treks, staff, or users by name or ID
-Can blacklist users or staff if required

---

### User (Trekker)

User can:
-Can register and log in
-Can view approved/open treks
-Can search and filter treks based on difficulty, location
Can book treks
Can view booking status and trekking history

The application prevents booking when no slots are available and allows booking only for Treks with Open status.

---

### Trek Staff

Trek Staff can register through the registration page.
A newly registered Staff account remains in pending status until approved by the Admin.

Trek Staff can:
-Can register and log in
-Need admin’s approval to access the dashboard
-Can view assigned treks by Admin
-Can update trek details such as:
-Available slots
-Trek status (Open/Closed)
-Can view list of users registered for their treks

---

## Database Design

The application uses SQLite as the database.
The main database tables are:

### User

Stores Admin, Staff and Trekker accounts.

Important fields:

- id
- username
- email
- password
- full_name
- phone
- role
- status
- bio
- created_at

The role field identifies whether the account belongs to an Admin, Staff member or User.

---

### Trek

Stores information about trekking events.

Important fields:

- id
- name
- location
- difficulty
- duration_days
- total_slots
- available_slots
- assigned_staff_id
- status
- start_date
- end_date
- description
- price
- altitude
- created_at
---

### Booking

Stores Trek booking information.

Important fields:

- id
- user_id
- trek_id
- booking_date
- status
- notes

A Booking connects a User with a Trek.

---

## Database Relationships

The main relationships are:

- One User can have many Bookings.
- One Trek can have many Bookings.
- One Staff member can be assigned to many Treks.
- Each Trek can have one assigned Staff member.

---

## Project Structure

    project/
    │
    ├── app.py
    ├── models.py
    ├── README.md
    │
    ├── instance/
    │   └── trekking.db
    │
    ├── templates/
    │   ├── base.html
    │   ├── login.html
    │   ├── register.html
    │   │
    │   ├── admin/
    │   │   ├── admin_dashboard.html
    │   │   ├── admin_treks.html
    │   │   ├── create_trek.html
    │   │   ├── edit_trek.html
    │   │   ├── assign_staff.html
    │   │   ├── admin_staff.html
    │   │   ├── admin_users.html
    │   │   ├── admin_bookings.html
    │   │   └── admin_search.html
    │   │
    │   ├── staff/
    │   │   ├── staff_dashboard.html
    │   │   ├── staff_manage_trek.html
    │   │   └── trek_participants.html
    │   │
    │   └── user/
    │       ├── user_dashboard.html
    │       ├── trek_details.html
    │       ├── my_bookings.html
    │       ├── trekking_history.html
    │       └── edit_profile.html
    │
    └── static/
        └── style.css

---

## Important Application Rules

1. Admin registration is not allowed.
2. Staff registration requires Admin approval.
3. Blacklisted Users and Staff cannot login.
4. Only Open Treks can be booked.
5. A Trek cannot be booked when available slots are zero.
6. Duplicate active booking of the same Trek is prevented.
7. Only assigned Staff can manage a Trek.
8. Cancelling a Booking returns one available slot to the Trek.
9. Booking records are retained for booking history.
10. When a Trek is completed, its active Bookings are marked as Completed.

---

## AI/LLM Declaration

AI/LLM tools were used for guidance, debugging assistance and understanding some programming concepts during development. The application was tested and reviewed to understand its main functionality, database models, routes, authentication flow and role-based operations.

---
