import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime

# Database connection function
def connect_to_db():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",  
            password="sk8er_gurnoor",  
            database="GymManagement"
        )
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# Function to execute queries
def execute_query(query, params=None, fetch=True):
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                result = cursor.fetchall()
                return result
            else:
                conn.commit()
                return True
        except Exception as e:
            st.error(f"Query execution error: {e}")
            return None
        finally:
            conn.close()
    return None

# Set page title
st.set_page_config(page_title="Gym Management System", layout="wide")

# Sidebar navigation
st.sidebar.title("Gym Management System")
page = st.sidebar.selectbox("Navigate", ["Home", "Members", "Trainers", "Payments", "Attendance", "Class Bookings"])

# Home page
if page == "Home":
    st.title("Gym Management System")
    st.write("Welcome to the Gym Management System. Use the sidebar to navigate through different sections.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quick Stats")
        # Get member count
        member_count = execute_query("SELECT COUNT(*) as count FROM Members")
        if member_count:
            st.metric("Total Members", member_count[0]['count'])
        
        # Get trainer count
        trainer_count = execute_query("SELECT COUNT(*) as count FROM Trainers")
        if trainer_count:
            st.metric("Total Trainers", trainer_count[0]['count'])
    
    with col2:
        st.subheader("Recent Payments")
        recent_payments = execute_query("""
            SELECT p.PaymentID, m.Name, p.Amount, p.Date, p.Status 
            FROM Payments p
            JOIN Members m ON p.MemberID = m.MemberID
            ORDER BY p.Date DESC LIMIT 5
        """)
        if recent_payments:
            st.dataframe(pd.DataFrame(recent_payments))

# Members page
elif page == "Members":
    st.title("Members Management")
    
    tab1, tab2 = st.tabs(["View Members", "Add Member"])
    
    with tab1:
        st.subheader("Current Members")
        members = execute_query("""
            SELECT m.MemberID, m.Name, m.Age, m.Gender, m.Phone, m.Email, 
                   m.MembershipType, t.Name as TrainerName
            FROM Members m
            LEFT JOIN Trainers t ON m.TrainerID = t.TrainerID
        """)
        if members:
            st.dataframe(pd.DataFrame(members))
        
        # Search functionality
        st.subheader("Search Member")
        search_term = st.text_input("Enter name to search")
        if search_term:
            search_results = execute_query("""
                SELECT m.MemberID, m.Name, m.Age, m.Gender, m.Phone, m.Email, 
                       m.MembershipType, t.Name as TrainerName
                FROM Members m
                LEFT JOIN Trainers t ON m.TrainerID = t.TrainerID
                WHERE m.Name LIKE %s
            """, (f"%{search_term}%",))
            if search_results:
                st.dataframe(pd.DataFrame(search_results))
            else:
                st.info("No members found matching your search.")
    
    with tab2:
        st.subheader("Add New Member")
        with st.form("add_member_form"):
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=15, max_value=80)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            address = st.text_area("Address")
            membership_type = st.selectbox("Membership Type", ["Monthly", "Quarterly", "Yearly"])
            
            # Get trainers for dropdown
            trainers = execute_query("SELECT TrainerID, Name FROM Trainers")
            if trainers:
                trainer_options = {t['Name']: t['TrainerID'] for t in trainers}
                trainer_options["None"] = None
                selected_trainer = st.selectbox("Assign Trainer", list(trainer_options.keys()))
                trainer_id = trainer_options[selected_trainer]
            else:
                trainer_id = None
                st.warning("No trainers available")
            
            submit_button = st.form_submit_button("Add Member")
            
            if submit_button:
                if not name or not phone or not email:
                    st.error("Name, phone and email are required fields.")
                else:
                    result = execute_query("""
                        INSERT INTO Members 
                        (Name, Age, Gender, Phone, Email, Address, MembershipType, TrainerID)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (name, age, gender, phone, email, address, membership_type, trainer_id), fetch=False)
                    
                    if result:
                        st.success("Member added successfully!")

# Trainers page
elif page == "Trainers":
    st.title("Trainers Management")
    
    tab1, tab2 = st.tabs(["View Trainers", "Add Trainer"])
    
    with tab1:
        st.subheader("Current Trainers")
        trainers = execute_query("""
            SELECT TrainerID, Name, Experience, Specialization, Phone, Salary
            FROM Trainers
        """)
        if trainers:
            st.dataframe(pd.DataFrame(trainers))
    
    with tab2:
        st.subheader("Add New Trainer")
        with st.form("add_trainer_form"):
            name = st.text_input("Name")
            experience = st.number_input("Experience (years)", min_value=0)
            specialization = st.text_input("Specialization")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])  # Added for the missing field
            phone = st.text_input("Phone")
            salary = st.number_input("Salary", min_value=0.0, step=100.0)
            
            submit_button = st.form_submit_button("Add Trainer")
            
            if submit_button:
                if not name or not phone or not specialization:
                    st.error("Name, phone and specialization are required fields.")
                else:
                    result = execute_query("""
                        INSERT INTO Trainers 
                        (Name, Experience, Specialization, Gender, Phone, Salary)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (name, experience, specialization, gender, phone, salary), fetch=False)
                    
                    if result:
                        st.success("Trainer added successfully!")

# Payments page
elif page == "Payments":
    st.title("Payments Management")
    
    tab1, tab2 = st.tabs(["View Payments", "Record Payment"])
    
    with tab1:
        st.subheader("Recent Payments")
        payments = execute_query("""
            SELECT p.PaymentID, m.Name as MemberName, p.Amount, 
                   p.Date, p.PaymentMethod, p.Status, p.ServiceType
            FROM Payments p
            JOIN Members m ON p.MemberID = m.MemberID
            ORDER BY p.Date DESC LIMIT 50
        """)
        if payments:
            st.dataframe(pd.DataFrame(payments))
            
        # Filter by status
        status_filter = st.selectbox("Filter by Status", ["All", "Completed", "Pending"])
        if status_filter != "All":
            filtered_payments = execute_query("""
                SELECT p.PaymentID, m.Name as MemberName, p.Amount, 
                       p.Date, p.PaymentMethod, p.Status, p.ServiceType
                FROM Payments p
                JOIN Members m ON p.MemberID = m.MemberID
                WHERE p.Status = %s
                ORDER BY p.Date DESC
            """, (status_filter,))
            if filtered_payments:
                st.dataframe(pd.DataFrame(filtered_payments))
    
    with tab2:
        st.subheader("Record New Payment")
        with st.form("add_payment_form"):
            # Get members for dropdown
            members = execute_query("SELECT MemberID, Name FROM Members")
            if members:
                member_options = {m['Name']: m['MemberID'] for m in members}
                selected_member = st.selectbox("Select Member", list(member_options.keys()))
                member_id = member_options[selected_member]
            else:
                member_id = None
                st.warning("No members available")
            
            amount = st.number_input("Amount", min_value=0.01, step=10.0)
            payment_method = st.selectbox("Payment Method", ["Cash", "Card", "Online"])
            status = st.selectbox("Status", ["Completed", "Pending"])
            service_type = st.selectbox("Service Type", ["Membership", "Class Booking", "Personal Training", "Other"])
            
            submit_button = st.form_submit_button("Record Payment")
            
            if submit_button:
                if not member_id or amount <= 0:
                    st.error("Please select a member and enter a valid amount.")
                else:
                    result = execute_query("""
                        INSERT INTO Payments 
                        (MemberID, Amount, PaymentMethod, Status, ServiceType)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (member_id, amount, payment_method, status, service_type), fetch=False)
                    
                    if result:
                        st.success("Payment recorded successfully!")

# Attendance page
elif page == "Attendance":
    st.title("Attendance Tracking")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Check-In Member")
        # Get members for dropdown
        members = execute_query("SELECT MemberID, Name FROM Members")
        if members:
            member_options = {m['Name']: m['MemberID'] for m in members}
            selected_member = st.selectbox("Select Member", list(member_options.keys()))
            
            if st.button("Check In"):
                result = execute_query("""
                    INSERT INTO Attendance (MemberID)
                    VALUES (%s)
                """, (member_options[selected_member],), fetch=False)
                
                if result:
                    st.success(f"Checked in {selected_member}")
    
    with col2:
        st.subheader("Check-Out Member")
        # Get members currently checked in
        checked_in = execute_query("""
            SELECT a.AttendanceID, m.Name, a.CheckInTime
            FROM Attendance a
            JOIN Members m ON a.MemberID = m.MemberID
            WHERE a.CheckOutTime IS NULL
        """)
        
        if checked_in:
            checkout_options = {f"{c['Name']} (since {c['CheckInTime']})": c['AttendanceID'] for c in checked_in}
            selected_checkout = st.selectbox("Select Member to Check Out", list(checkout_options.keys()))
            
            if st.button("Check Out"):
                result = execute_query("""
                    UPDATE Attendance
                    SET CheckOutTime = CURRENT_TIMESTAMP
                    WHERE AttendanceID = %s
                """, (checkout_options[selected_checkout],), fetch=False)
                
                if result:
                    st.success(f"Checked out {selected_checkout.split(' (')[0]}")
        else:
            st.info("No members currently checked in")
    
    st.subheader("Today's Attendance")
    today_attendance = execute_query("""
        SELECT m.Name, a.CheckInTime, a.CheckOutTime,
               TIMEDIFF(IFNULL(a.CheckOutTime, NOW()), a.CheckInTime) as Duration
        FROM Attendance a
        JOIN Members m ON a.MemberID = m.MemberID
        WHERE DATE(a.CheckInTime) = CURDATE()
        ORDER BY a.CheckInTime DESC
    """)
    
    if today_attendance:
        st.dataframe(pd.DataFrame(today_attendance))
    else:
        st.info("No attendance records for today")

# Class Bookings page
elif page == "Class Bookings":
    st.title("Class Bookings")
    
    tab1, tab2 = st.tabs(["View Bookings", "Add Booking"])
    
    with tab1:
        st.subheader("Upcoming Class Bookings")
        upcoming_bookings = execute_query("""
            SELECT cb.BookingID, m.Name as MemberName, t.Name as TrainerName,
                   cb.ClassDate, cb.StartTime, cb.EndTime
            FROM ClassBookings cb
            JOIN Members m ON cb.MemberID = m.MemberID
            JOIN Trainers t ON cb.TrainerID = t.TrainerID
            WHERE cb.ClassDate >= CURDATE()
            ORDER BY cb.ClassDate, cb.StartTime
        """)
        
        if upcoming_bookings:
            st.dataframe(pd.DataFrame(upcoming_bookings))
        else:
            st.info("No upcoming class bookings")
        
        # Filter by date
        selected_date = st.date_input("Filter by Date")
        if selected_date:
            date_bookings = execute_query("""
                SELECT cb.BookingID, m.Name as MemberName, t.Name as TrainerName,
                       cb.ClassDate, cb.StartTime, cb.EndTime
                FROM ClassBookings cb
                JOIN Members m ON cb.MemberID = m.MemberID
                JOIN Trainers t ON cb.TrainerID = t.TrainerID
                WHERE cb.ClassDate = %s
                ORDER BY cb.StartTime
            """, (selected_date,))
            
            if date_bookings:
                st.dataframe(pd.DataFrame(date_bookings))
            else:
                st.info(f"No class bookings for {selected_date}")
    
    with tab2:
        st.subheader("Book a New Class")
        with st.form("add_booking_form"):
            # Get members for dropdown
            members = execute_query("SELECT MemberID, Name FROM Members")
            if members:
                member_options = {m['Name']: m['MemberID'] for m in members}
                selected_member = st.selectbox("Select Member", list(member_options.keys()))
                member_id = member_options[selected_member]
            else:
                member_id = None
                st.warning("No members available")
            
            # Get trainers for dropdown
            trainers = execute_query("SELECT TrainerID, Name FROM Trainers")
            if trainers:
                trainer_options = {t['Name']: t['TrainerID'] for t in trainers}
                selected_trainer = st.selectbox("Select Trainer", list(trainer_options.keys()))
                trainer_id = trainer_options[selected_trainer]
            else:
                trainer_id = None
                st.warning("No trainers available")
            
            class_date = st.date_input("Class Date")
            start_time = st.time_input("Start Time")
            end_time = st.time_input("End Time")
            
            submit_button = st.form_submit_button("Book Class")
            
            if submit_button:
                if not member_id or not trainer_id:
                    st.error("Please select both member and trainer.")
                elif end_time <= start_time:
                    st.error("End time must be after start time.")
                else:
                    result = execute_query("""
                        INSERT INTO ClassBookings 
                        (MemberID, TrainerID, ClassDate, StartTime, EndTime)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (member_id, trainer_id, class_date, start_time, end_time), fetch=False)
                    
                    if result:
                        st.success("Class booked successfully!")

# Run the app with: streamlit run app.py