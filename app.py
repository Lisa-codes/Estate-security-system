from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import hashlib
from datetime import datetime


app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database connection function
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        port=3307,  # Change this if your MySQL runs on a different port
        user="devlisa",
        password="Devnjeri03$",
        database="wakigwe_db",
        cursorclass=pymysql.cursors.DictCursor
    )

# Routes
@app.route('/')
def index():
    return render_template('index.html')

#  Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            print("❌ Passwords do not match!")
            return "Passwords do not match!", 400

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        print(f"🔹 Hashed Password: {hashed_password}")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username exists
        cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            print("❌ Username already exists!")
            return "Username already exists!", 400

        print("✅ Inserting user into database...")

        # Insert into user table
        cursor.execute(
            "INSERT INTO user (username, role, password) VALUES (%s, %s, %s)",
            (username, role, hashed_password)
        )

        # Insert into registration table
        cursor.execute(
            "INSERT INTO registration (username, role, password) VALUES (%s, %s, %s)",
            (username,role,hashed_password)
        )
        conn.commit()

        print("✅ User registered successfully!")

        cursor.close()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user details
        cursor.execute("SELECT username, role, password FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            stored_hashed_password = user['password']  # Hashed password from DB
            hashed_input_password = hashlib.sha256(password.encode()).hexdigest()

            if hashed_input_password == stored_hashed_password:
                session['username'] = user['username']
                session['role'] = user['role']

                #  Redirect based on role
                if user['role'] == 'admin':
                    return redirect(url_for('admin_panel'))
                elif user['role'] == 'guard':
                    return redirect(url_for('report_panel'))

        return "Invalid credentials!", 401  # Incorrect username/password

    return render_template('login.html')

#  Admin Panel Route 
# Admin Panel Route - Displays all reports
@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all reports
    cursor.execute("SELECT * FROM reports ORDER BY created_at DESC")
    reports = cursor.fetchall()

    cursor.close()
    conn.close()

    # Pass reports to the admin panel template
    return render_template('admin_panel.html', reports=reports)


#  Report Panel Route 
@app.route('/report_panel')
def report_panel():
    if 'username' not in session or session['role'] != 'guard':
        return redirect(url_for('login'))
    return render_template('report_panel.html') 

#submit reports to database route
@app.route('/submit_report', methods=['POST'])
def submit_report():
    if 'username' not in session or session['role'] != 'guard':
        return redirect(url_for('login'))  # Redirect if not logged in as guard

    # Debugging: Print received form data
    print("Received form data:", request.form)

    # Extract data safely using `.get()`
    incident_category = request.form.get('incident-category')
    new_category = request.form.get('new-category')
    description = request.form.get('description')
    location = request.form.get('location')
    resident_name = request.form.get('resident-name')
    guard_name = session['username']  # Automatically use logged-in guard's username
    date_time = request.form.get('date-time')

    # Check for missing fields
    if not incident_category or not description or not location or not date_time:
        return "Error: Some fields are missing. Please fill out all required fields.", 400

    # Insert into database
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports (incident_category, new_category, description, location, resident_name, guard_name, date_time) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (incident_category, new_category, description, location, resident_name, guard_name, date_time))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('guard_incident_history'))  # Redirect to incident history after submitting

#incident history route
@app.route('/guard_incident_history')
def guard_incident_history():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY created_at DESC")  # Fetch all reports
    reports = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('guard_incident_history.html', reports=reports)


#mark as handled route
@app.route('/mark_as_handled/<int:report_id>', methods=['POST'])
def mark_as_handled(report_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Update status to 'Handled'
    cursor.execute("UPDATE reports SET status = 'Handled' WHERE id = %s", (report_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('admin_panel'))  # Refresh admin panel

#admin analytics route
@app.route('/admin_analytics')
def admin_analytics():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Incident Frequency
    cursor.execute("SELECT incident_category, COUNT(*) FROM reports GROUP BY incident_category ORDER BY COUNT(*) DESC")
    incident_data = cursor.fetchall()
    incident_categories = [row['incident_category'] for row in incident_data]
    incident_counts = [row['COUNT(*)'] for row in incident_data]

    # Most Active Guards
    cursor.execute("SELECT guard_name, COUNT(*) FROM reports GROUP BY guard_name ORDER BY COUNT(*) DESC LIMIT 5")
    guard_data = cursor.fetchall()
    guard_names = [row['guard_name'] for row in guard_data]
    guard_activity_counts = [row['COUNT(*)'] for row in guard_data]

    # Location-Based Analysis
    cursor.execute("SELECT location, COUNT(*) FROM reports GROUP BY location ORDER BY COUNT(*) DESC LIMIT 5")
    location_data = cursor.fetchall()
    locations = [row['location'] for row in location_data]
    location_counts = [row['COUNT(*)'] for row in location_data]

    # General Summary
    highest_category = incident_categories[0] if incident_categories else "No incidents reported"
    most_active_guard = guard_names[0] if guard_names else "No guards reported incidents"
    most_reported_location = locations[0] if locations else "No location data available"
    
    summary = [
        f"Highest reported incident: {highest_category}",
        f"Most active guard: {most_active_guard}",
        f"Most reported location: {most_reported_location}",
        f"Total incidents recorded: {sum(incident_counts)}"
    ]

    cursor.close()
    conn.close()

    return render_template(
        'admin_analytics.html',
        incident_categories=incident_categories,
        incident_counts=incident_counts,
        guard_names=guard_names,
        guard_activity_counts=guard_activity_counts,
        locations=locations,
        location_counts=location_counts,
        summary=summary
    )

#delete accounts
@app.route('/delete_accounts')
def delete_accounts():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, role FROM user")  # Adjust table name if needed
            user = cursor.fetchall()
    finally:
        connection.close()
    
    return render_template('delete_accounts.html', user=user)

# Route to delete an account
@app.route('/delete_account/<int:user_id>', methods=['POST'])
def delete_account(user_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
            connection.commit()
            flash("Account deleted successfully!", "success")
    except pymysql.MySQLError as e:
        flash(f"Error deleting account: {str(e)}", "danger")
    finally:
        connection.close()

    return redirect(url_for('delete_accounts'))

#  Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
