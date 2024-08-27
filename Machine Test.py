import mysql.connector
from mysql.connector import Error
import datetime
import random
import string
import re


# Function to create a database connection
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='faith',
            database='hotel_booking_system'
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None


# Function to create tables in the database
def create_tables(connection):
    try:
        cursor = connection.cursor()

        # Create rooms table with status field
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                room_id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(20) NOT NULL,
                room_number INT NOT NULL,
                rate_per_day DECIMAL(10, 2) NOT NULL,
                is_hourly_rate BOOLEAN DEFAULT FALSE,
                status ENUM('occupied', 'unoccupied') DEFAULT 'unoccupied' NOT NULL
            )
        """)

        # Create customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(20)
            )
        """)

        # Create bookings table with foreign keys
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id VARCHAR(10) PRIMARY KEY,
                customer_id INT NOT NULL,
                room_id INT NOT NULL,
                date_of_booking DATE NOT NULL,
                date_of_occupancy DATE NOT NULL,
                no_of_days INT NOT NULL,
                advance_received DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (room_id) REFERENCES rooms(room_id)
            )
        """)

        # Create Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(50) NOT NULL,
                role ENUM('admin', 'member') NOT NULL
            )
        """)

        connection.commit()
        print("Tables created successfully.")
    except Error as e:
        print(f"Error: {e}")


# Function to validate the password
def validate_password(password):
    if len(password) < 8:
        print("Password must be at least 8 characters long.")
        return False
    if not re.search(r'[A-Za-z]', password):
        print("Password must contain at least one letter.")
        return False
    if not re.search(r'[0-9]', password):
        print("Password must contain at least one number.")
        return False
    return True


# Function to register a new user
def register(connection):
    try:
        cursor = connection.cursor()
        while True:
            print("Register your details here.")

            # Validate username
            while True:
                username = input("Create a username (alphanumeric): ")
                if not username.isalnum():
                    print("Username must be alphanumeric (letters and numbers only).")
                else:
                    cursor.execute("SELECT * FROM Users WHERE username=%s", (username,))
                    if cursor.fetchone():
                        print("Username already exists, please choose another.")
                    else:
                        break

            # Validate password
            while True:
                password = input("Enter the password: ")
                if validate_password(password):
                    break

            # Assign role based on username (for simplicity)
            if username.lower().startswith('admin'):
                role = 'admin'
            else:
                role = 'member'

            # Insert validated data into the database
            insert_query = "INSERT INTO Users (username, password, role) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (username, password, role))
            connection.commit()
            print(f"You have successfully registered as a {role}!")
            break
    except Error as e:
        print("Error:", e)


# Function to validate login credentials
def login(connection):
    try:
        cursor = connection.cursor()
        username = input("Enter username: ")
        password = input("Enter password: ")

        cursor.execute("SELECT * FROM Users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            print("Login successful!")
            if user[3] == 'admin':  # Assuming role is the 4th field in the Users table
                admin_menu(connection)
            else:
                print("Welcome, member!")
                # Implement member functionalities here if needed
        else:
            print("Invalid username or password.")
    except Error as e:
        print("Error:", e)


# Function to generate a booking ID
def generate_booking_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


# Function to display category wise list of rooms and their rate per day
def category_list(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT category, room_number, rate_per_day FROM rooms")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Category: {row[0]}, Room Number: {row[1]}, Rate per Day: ${row[2]:.2f}")
    except Error as e:
        print(f"Error: {e}")


# Function to list all rooms which are occupied for the next two days
def occupied_room_list(connection):
    try:
        today = datetime.date.today()
        two_days_later = today + datetime.timedelta(days=2)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT r.category, r.room_number, b.date_of_occupancy, b.no_of_days 
            FROM rooms r 
            JOIN bookings b ON r.room_id = b.room_id
            WHERE b.date_of_occupancy <= %s AND (b.date_of_occupancy + INTERVAL b.no_of_days DAY) >= %s
        """, (two_days_later, today))
        rows = cursor.fetchall()
        for row in rows:
            print(f"Category: {row[0]}, Room Number: {row[1]}, Occupied From: {row[2]}, Days: {row[3]}")
    except Error as e:
        print(f"Error: {e}")


# Function to display list of rooms in increasing order of rate per day
def list_of_rooms_pricewise(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT category, room_number, rate_per_day FROM rooms ORDER BY rate_per_day ASC")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Category: {row[0]}, Room Number: {row[1]}, Rate per Day: ${row[2]:.2f}")
    except Error as e:
        print(f"Error: {e}")


# Function to search rooms based on BookingID and display customer details
def search_by_booking_id(connection):
    booking_id = input("Enter Booking ID: ")
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT b.booking_id, c.customer_name, r.category, r.room_number, b.date_of_booking, b.date_of_occupancy, b.no_of_days, b.advance_received
            FROM bookings b
            JOIN rooms r ON b.room_id = r.room_id
            JOIN customers c ON b.customer_id = c.customer_id
            WHERE b.booking_id = %s
        """, (booking_id,))
        row = cursor.fetchone()
        if row:
            print(f"Booking ID: {row[0]}")
            print(f"Customer Name: {row[1]}")
            print(f"Category: {row[2]}, Room Number: {row[3]}")
            print(f"Date of Booking: {row[4]}")
            print(f"Date of Occupancy: {row[5]}")
            print(f"No of Days: {row[6]}")
            print(f"Advance Received: ${row[7]:.2f}")
        else:
            print("No record found.")
    except Error as e:
        print(f"Error: {e}")


# Function to display rooms which are not booked
def unoccupied_rooms(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT category, room_number FROM rooms WHERE status = 'unoccupied'")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Category: {row[0]}, Room Number: {row[1]}")
    except Error as e:
        print(f"Error: {e}")


# Function to update room status when the customer leaves
def update_rooms(connection):
    booking_id = input("Enter Booking ID to update: ")
    try:
        cursor = connection.cursor()

        # Update room status to unoccupied after customer leaves
        cursor.execute("""
            UPDATE rooms 
            SET status = 'unoccupied'
            WHERE room_id = (SELECT room_id FROM bookings WHERE booking_id = %s)
        """, (booking_id,))

        # Delete the booking record
        cursor.execute("DELETE FROM bookings WHERE booking_id = %s", (booking_id,))
        connection.commit()
        print("Room status updated to unoccupied.")
    except Error as e:
        print(f"Error: {e}")


# Function to store records in a file and display from the file
def store_and_display_records(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM bookings")
        rows = cursor.fetchall()
        with open('bookings.txt', 'w') as file:
            for row in rows:
                file.write(str(row) + '\n')
        print("Records stored in bookings.txt")

        # Display records from the file
        with open('bookings.txt', 'r') as file:
            for line in file:
                print(line.strip())
    except Error as e:
        print(f"Error: {e}")


# Function to book a room
def book_room(connection):
    try:
        cursor = connection.cursor()

        # Display rooms
        category_list(connection)

        room_number = int(input("Enter room number to book: "))
        customer_name = input("Enter customer name: ")
        phone_number = input("Enter customer phone number: ")
        advance_received = float(input("Enter advance received: "))

        # Check if room exists and is unoccupied
        cursor.execute("SELECT room_id, status FROM rooms WHERE room_number = %s", (room_number,))
        room = cursor.fetchone()
        if not room:
            print("Room not found.")
            return
        if room[1] == 'occupied':
            print("Room is already occupied.")
            return

        room_id = room[0]

        # Insert customer if not exists
        cursor.execute("SELECT customer_id FROM customers WHERE phone_number = %s", (phone_number,))
        customer = cursor.fetchone()
        if customer:
            customer_id = customer[0]
        else:
            cursor.execute("INSERT INTO customers (customer_name, phone_number) VALUES (%s, %s)",
                           (customer_name, phone_number))
            connection.commit()
            cursor.execute("SELECT customer_id FROM customers WHERE phone_number = %s", (phone_number,))
            customer_id = cursor.fetchone()[0]

        # Book room
        booking_id = generate_booking_id()
        date_of_booking = datetime.date.today()
        date_of_occupancy = input("Enter date of occupancy (YYYY-MM-DD): ")
        no_of_days = int(input("Enter number of days: "))

        cursor.execute("""
            INSERT INTO bookings (booking_id, customer_id, room_id, date_of_booking, date_of_occupancy, no_of_days, advance_received)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (booking_id, customer_id, room_id, date_of_booking, date_of_occupancy, no_of_days, advance_received))

        # Update the room status to 'occupied'
        cursor.execute("UPDATE rooms SET status = 'occupied' WHERE room_id = %s", (room_id,))

        connection.commit()
        print("Room booked successfully!")
    except Error as e:
        print(f"Error: {e}")


# Admin menu function
def admin_menu(connection):
    while True:
        print("\nAdmin Menu")
        print("1. List of Room Categories and Their Rates")
        print("2. List of Occupied Rooms for Next Two Days")
        print("3. List of Rooms Pricewise")
        print("4. Search by Booking ID")
        print("5. List of Unoccupied Rooms")
        print("6. Update Room Status")
        print("7. Store and Display Records")
        print("8. Book a Room")
        print("9. Logout")

        choice = input("Enter your choice: ")

        if choice == '1':
            category_list(connection)
        elif choice == '2':
            occupied_room_list(connection)
        elif choice == '3':
            list_of_rooms_pricewise(connection)
        elif choice == '4':
            search_by_booking_id(connection)
        elif choice == '5':
            unoccupied_rooms(connection)
        elif choice == '6':
            update_rooms(connection)
        elif choice == '7':
            store_and_display_records(connection)
        elif choice == '8':
            book_room(connection)
        elif choice == '9':
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")


# Main function to drive the program
def main():
    connection = create_connection()
    if connection:
        create_tables(connection)
        while True:
            print("\nHotel Booking System")
            print("1. Register")
            print("2. Login")
            print("3. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                register(connection)
            elif choice == '2':
                login(connection)
            elif choice == '3':
                print("Exiting the system.")
                connection.close()
                break
            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
