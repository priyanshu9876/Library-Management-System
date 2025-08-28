from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection setup
client = None
db = None

# Try connecting to MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB URI if needed
    db = client['library_db']  # Use your database name
    print("MongoDB connected successfully.")
except ConnectionError as e:
    print("Failed to connect to MongoDB:", e)


# Hardcoded users collection in MongoDB (can be fetched from db)
users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user': {'password': 'user123', 'role': 'user'}
}

@app.route('/')
def home():
    return render_template('index.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Debugging: Check if both fields are provided
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return redirect(url_for('login'))

        # Search for the user in the database by name (not username)
        user = db.users.find_one({'name': username})  # Searching by 'name' instead of 'username'

        # Debugging: Check if the user exists
        if not user:
            flash(f"Username '{username}' not found. Please check your username.", 'error')
            return redirect(url_for('login'))

        # Check if password matches (no hashing for now, plain text comparison)
        if user and user['password'] == password:
            # Debugging: Set session variables
            session['username'] = user['name']  # Storing 'name' as 'username'
            session['role'] = 'admin' if user.get('is_admin') else 'user'  # Role check

            # Debugging: Print session details
            print(f"User {user['name']} logged in as {session['role']}")

            # Redirect based on user role
            if user['is_admin']:
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('user_page'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return redirect(url_for('home'))

    # Render the login page for GET requests
    return render_template('index.html')




@app.route('/admin')
def admin_page():
    if session.get('role') == 'admin':
        # Access the 'books' collection
        books_collection = db['books']

        # Query the books from the collection (fetching all books)
        books = books_collection.find()

        # Convert MongoDB cursor to a list for rendering in the template
        books_list = list(books)

        # Pass books data to the template
        return render_template('admin.html', username=session['username'], books=books_list)
    else:
        flash('Unauthorized access!')
        return redirect(url_for('home'))


@app.route('/user')
def user_page():
    if session.get('role') == 'user':
        return render_template('user.html', username=session['username'])
    else:
        flash('Unauthorized access!')
        return redirect(url_for('home'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/home')
def home_redirect():
    if 'username' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_page'))
        elif role == 'user':
            return redirect(url_for('user_page'))
    return redirect(url_for('home'))

@app.route('/admin_book_issue', methods=['GET', 'POST'])
def admin_book_issue():
    if session.get('role') == 'admin':  # Ensure the user is an admin
        if request.method == 'POST':
            # Get form data
            book_name = request.form.get('book_name').strip().lower()
            issue_date = request.form.get('issue_date')
            return_date = request.form.get('return_date')
            remarks = request.form.get('remarks')

            # Check if the book exists and is available
            book = db.books.find_one({'name': {'$regex': book_name, '$options': 'i'}})

            if book:
                if book['status'] == 'available':
                    # Update book status to 'issued'
                    db.books.update_one({'_id': book['_id']}, {'$set': {'status': 'issued'}})

                    # Record the transaction in the 'transactions' collection
                    transaction = {
                        'book_name': book_name,
                        'issue_date': issue_date,
                        'return_date': return_date,
                        'remarks': remarks,
                        'status': 'issued'
                    }
                    db.transactions.insert_one(transaction)

                    flash(f"The book '{book_name}' has been successfully issued.", 'success')
                else:
                    flash(f"The book '{book_name}' is already issued.", 'error')
            else:
                flash(f"The book '{book_name}' was not found in the library.", 'error')

            return redirect(url_for('admin_book_issue'))  # Redirect to the same page to show messages

        return render_template('admin_bookIssue.html')  # Render the form if the request is GET

    else:
        flash('Unauthorized access! You must be an admin to access this page.', 'error')
        return redirect(url_for('home')) 


@app.route('/user_book_issue', methods=['GET', 'POST'])
def user_book_issue():
    if session.get('role') == 'user':  # Ensure the user has 'user' role
        if request.method == 'POST':
            # Get form data
            book_name = request.form.get('book_name').strip().lower()
            issue_date = request.form.get('issue_date')
            return_date = request.form.get('return_date')
            remarks = request.form.get('remarks')

            # Check if the book exists and is available
            book = db.books.find_one({'name': {'$regex': book_name, '$options': 'i'}})

            if book:
                if book['status'] == 'available':
                    # Update book status to 'issued'
                    db.books.update_one({'_id': book['_id']}, {'$set': {'status': 'issued'}})

                    # Record the transaction in the 'transactions' collection
                    transaction = {
                        'book_name': book_name,
                        'user_id': session.get('user_id'),  # Assuming user ID is stored in the session
                        'issue_date': issue_date,
                        'return_date': return_date,
                        'remarks': remarks,
                        'status': 'issued'
                    }
                    db.transactions.insert_one(transaction)

                    flash(f"The book '{book_name}' has been successfully issued.", 'success')
                else:
                    flash(f"The book '{book_name}' is already issued.", 'error')
            else:
                flash(f"The book '{book_name}' was not found in the library.", 'error')

            return redirect(url_for('user_book_issue'))  # Redirect to the same page to show messages

        return render_template('user_bookIssue.html')  # Render the form if the request is GET

    else:
        flash('Unauthorized access! You must be a registered user to access this page.', 'error')
        return redirect(url_for('home'))  # Redirect to home if the user is not authorized


@app.route('/transactions')
def transactions_page():
    if 'role' in session:
        role = session['role']
        if role == 'admin':
            return render_template('admin_transactions.html')
        elif role == 'user':
            return render_template('user_transactions.html')
    flash('Please log in to access transactions.')
    return redirect(url_for('home'))


# Route for checking book availability (redirect to search page)
@app.route('/search_results', methods=['GET', 'POST'])
def search_results():
    if request.method == 'POST':
        # Get book name from the form
        book_name = request.form.get('book_name', '').strip()

        # Check if book_name is provided
        if not book_name:
            flash("Please enter a book name.", "error")
            return redirect(url_for('search_form'))

        # Search for the book in the database
        book = db.books.find_one({'name': {'$regex': book_name, '$options': 'i'}})

        # Check if the book is found
        if book:
            # Book is found, return the availability
            availability = "Available" if book.get('status') == 'available' else "Not Available"
            return render_template('search_results.html', book_name=book_name, availability=availability)
        else:
            # Book not found, flash a message and redirect to the search form
            flash("Book not found in the library.", "error")
            return redirect(url_for('search_form'))

    else:
        # Handle GET request (when accessed directly)
        return redirect(url_for('search_form'))


@app.route('/search_form', methods=['GET'])
def search_form():
    return render_template('search_form.html')


@app.route('/admin/returnbook', methods=['GET', 'POST'])
def admin_returnbook():
    if request.method == 'POST':
        # Get form data
        book_name = request.form.get('returnBookName')  # Matches 'name' attribute in the form
        return_date = request.form.get('returnDate')  # Matches 'name' attribute in the form
        remarks = request.form.get('remarks', '').strip()  # Matches 'name' attribute in the form

        # Check for required fields
        if not book_name or not return_date:
            flash("Book name and return date are required.", 'error')
            return redirect(url_for('admin_returnbook'))

        # Find the book in the database
        book = db.books.find_one({'name': {'$regex': f'^{book_name}$', '$options': 'i'}})

        if book:
            # Check if the book is currently issued
            if book.get('status') == 'issued':
                # Update book status to 'available' in the books collection
                db.books.update_one(
                    {'_id': book['_id']},
                    {'$set': {'status': 'available'}}
                )

                # Log the transaction with status 'returned' in the transactions collection
                transaction = {
                    'book_name': book_name,
                    'status': 'returned',
                    'return_date': return_date,
                    'remarks': remarks,
                    'user_id': session.get('user_id'),  # Assuming a session system is used
                    
                }
                db.transactions.insert_one(transaction)

                flash(f"Book '{book_name}' returned successfully.", 'success')
            else:
                flash(f"Book '{book_name}' is not currently issued.", 'error')
        else:
            flash(f"Book '{book_name}' not found in the library database.", 'error')

        # Redirect to the admin transactions page after processing
        return redirect(url_for('transactions_page'))

    # Render the return book form for GET requests
    return render_template('admin_returnbook.html')

fines = db['fines']  # Reference to the fines collection

from datetime import datetime, date

def convert_to_str(date_obj):
    """Convert date object (datetime.date or datetime.datetime) to string."""
    if isinstance(date_obj, (datetime, date)):
        return date_obj.strftime('%Y-%m-%d')
    else:
        return str(date_obj)  # Fallback to string if it's neither

@app.route('/admin/payfine', methods=['GET', 'POST'])
def admin_payfine():
    if request.method == 'POST':
        # Get data from the form
        book_name = request.form['book name']
        return_date = datetime.strptime(request.form['returnDate'], '%Y-%m-%d').date()
        actual_return_date = datetime.strptime(request.form['actualReturnDate'], '%Y-%m-%d').date()
        fine_paid = 'finePaid' in request.form  # Checkbox for fine paid
        remarks = request.form['remarks']

        # Convert dates to strings for MongoDB storage
        return_date_str = convert_to_str(return_date)
        actual_return_date_str = convert_to_str(actual_return_date)

        # Calculate the fine if the actual return date is after the return date
        fine_calculated = 0
        if actual_return_date > return_date:
            diff_in_time = (actual_return_date - return_date).days
            fine_calculated = diff_in_time * 50  # ₹50 per day late

        # Store the fine details in the fines collection
        fines.insert_one({
            'book_name': book_name,
            'return_date': return_date_str,
            'actual_return_date': actual_return_date_str,
            'fine_calculated': fine_calculated,
            'fine_paid': fine_paid,
            'remarks': remarks,
            'created_at': datetime.now()  # Timestamp for record creation
        })

        # Redirect to the admin page or any other page as needed
        return redirect(url_for('admin_page'))

    return render_template('admin_payfine.html')
 # This template contains the form


@app.route('/user/payfine', methods=['GET', 'POST'])
def user_payfine():
    if request.method == 'POST':
        # Get data from the form
        book_name = request.form['book name']
        return_date = datetime.strptime(request.form['returnDate'], '%Y-%m-%d').date()
        actual_return_date = datetime.strptime(request.form['actualReturnDate'], '%Y-%m-%d').date()
        fine_paid = 'finePaid' in request.form  # Checkbox for fine paid
        remarks = request.form['remarks']

        # Convert dates to strings for MongoDB storage
        return_date_str = convert_to_str(return_date)
        actual_return_date_str = convert_to_str(actual_return_date)

        # Calculate the fine if the actual return date is after the return date
        fine_calculated = 0
        if actual_return_date > return_date:
            diff_in_time = (actual_return_date - return_date).days
            fine_calculated = diff_in_time * 50  # ₹50 per day late

        # Store the fine details in the fines collection
        fines.insert_one({
            'book_name': book_name,
            'return_date': return_date_str,
            'actual_return_date': actual_return_date_str,
            'fine_calculated': fine_calculated,
            'fine_paid': fine_paid,
            'remarks': remarks,
            'created_at': datetime.now()  # Timestamp for record creation
        })

        # Redirect to the user profile or another page
        return redirect(url_for('user_profile'))

    # Render the form if it's a GET request
    return render_template('user_payfine.html')


@app.route('/maintenance', methods=['GET'])
def maintenance_home():
    return render_template('maintenance_home.html')

memberships = db['memberships']  # Access the 'memberships' collection


@app.route('/add_membership', methods=['GET', 'POST'])
def add_membership():
    if request.method == 'POST':
        # Get data from the form
        user_name = request.form.get('userName')
        membership_type = request.form.get('membershipType')
        joining_date = request.form.get('joiningDate')
        
        # Validate input
        if not user_name or not membership_type or not joining_date:
            error_message = "All fields are required. Please fill in all the details."
            return render_template('add_membership.html', error_message=error_message)
        
        # Parse the joining date
        joining_date = datetime.strptime(joining_date, '%Y-%m-%d')
        
        # Calculate the last date of membership based on the membership type
        if membership_type == '6_months':
            last_date = joining_date + timedelta(days=6 * 30)  # Approx. 6 months
        elif membership_type == '1_year':
            last_date = joining_date + timedelta(days=365)
        elif membership_type == '2_years':
            last_date = joining_date + timedelta(days=2 * 365)
        else:
            error_message = "Invalid membership type selected."
            return render_template('add_membership.html', error_message=error_message)
        
        # Store the data in MongoDB
        memberships.insert_one({
            'user_name': user_name,
            'membership_type': membership_type,
            'joining_date': joining_date.strftime('%Y-%m-%d'),
            'last_date': last_date.strftime('%Y-%m-%d')
        })
        
        # Redirect to a maintenance or success page
        return redirect(url_for('maintenance_home'))
        
    return render_template('add_membership.html')


@app.route('/update_membership', methods=['GET', 'POST'])
def update_membership():
    if request.method == 'POST':
        # Retrieve form data
        user_name = request.form.get('userName')  # Updated to user_name
        membership_extension = request.form.get('membershipExtension')

        if not user_name:
            error_message = "Please enter the user name."
            return render_template('update_membership.html', error_message=error_message)

        # Find the user's membership in the database
        membership = db.memberships.find_one({'user_name': user_name})

        if not membership:
            error_message = f"No membership found for user: {user_name}."
            return render_template('update_membership.html', error_message=error_message)

        # Extract existing joining and last dates
        joining_date = datetime.strptime(membership['joining_date'], '%Y-%m-%d')
        last_date = datetime.strptime(membership['last_date'], '%Y-%m-%d')

        if membership_extension == "six_months":
            new_last_date = last_date + timedelta(days=182)  # Extend by 6 months
            new_membership_type = "6_months"
            success_message = f"Membership for {user_name} extended by six months."
        elif membership_extension == "one_year":
            new_last_date = last_date + timedelta(days=365)  # Extend by 1 year
            new_membership_type = "1_year"
            success_message = f"Membership for {user_name} extended by one year."
        elif membership_extension == "two_years":
            new_last_date = last_date + timedelta(days=730)  # Extend by 2 years
            new_membership_type = "2_years"
            success_message = f"Membership for {user_name} extended by two years."
        elif membership_extension == "remove_membership":
            # Delete the membership record
            db.memberships.delete_one({'user_name': user_name})
            success_message = f"Membership for {user_name} removed successfully."
            flash(success_message, 'success')
            return redirect(url_for('maintenance_home'))
        else:
            error_message = "Invalid membership action selected."
            return render_template('update_membership.html', error_message=error_message)

        # Update the existing membership details in the database
        db.memberships.update_one(
            {'user_name': user_name},
            {
                '$set': {
                    'last_date': new_last_date.strftime('%Y-%m-%d'),
                    'membership_type': new_membership_type
                }
            }
        )

        flash(success_message, 'success')
        return redirect(url_for('maintenance_home'))

    # Fetch all memberships to display in the form
    memberships = db.memberships.find()
    return render_template('update_membership.html', memberships=memberships)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    # Check if the database connection is established
    if db is None:
        return "Database connection failed. Please check MongoDB setup.", 500

    if request.method == 'POST':
        # Retrieve form data
        media_type = request.form.get('mediaType', '').strip()
        book_movie_name = request.form.get('bookMovieName', '').strip()
        procurement_date = request.form.get('procurementDate', '').strip()
        quantity = request.form.get('quantity', '').strip()

        # Validate input fields
        if not media_type or not book_movie_name or not procurement_date or not quantity:
            flash("All fields are required.", "error")
            return render_template('add_book.html')  # Re-render the form with error message

        # Validate quantity
        try:
            quantity = int(quantity)
            if quantity <= 0:
                flash("Quantity must be a positive integer.", "error")
                return render_template('add_book.html')  # Re-render the form with error message
        except ValueError:
            flash("Quantity must be a valid integer.", "error")
            return render_template('add_book.html')  # Re-render the form with error message

        try:
            # Insert data into MongoDB
            book_data = {
                'media_type': media_type,
                'name': book_movie_name,
                'procurement_date': procurement_date,
                'quantity': quantity,
                'status': 'available'
            }

            result = db.books.insert_one(book_data)

            # Verify insertion
            if result.inserted_id:
                flash("Book added successfully!", "success")
                return redirect(url_for('success_page'))  # Redirect to a success page
            else:
                flash("Failed to add the book to the database.", "error")
                return render_template('add_book.html')  # Re-render the form with error message

        except Exception as e:
            print(f"Error adding book to database: {e}")
            flash("An unexpected error occurred while adding the book.", "error")
            return render_template('add_book.html')  # Re-render the form with error message

    # Render the form for GET requests
    return render_template('add_book.html')

@app.route('/success')
def success_page():
    return "Book added successfully!"

@app.route('/update_book', methods=['GET', 'POST'])
def update_book():
    if request.method == 'POST':
        # Retrieve form data with default values for safety
        original_name = request.form.get('originalName', '').strip()  # Original book name
        new_name = request.form.get('newName', '').strip()            # Updated book name (optional)
        media_type = request.form.get('mediaType', '').strip()        # Media type
        procurement_date = request.form.get('procurementDate', '').strip()  # Procurement date
        status = request.form.get('status', '').strip()               # Status
        delete_book = 'deleteBook' in request.form  # Checkbox for deleting the book

        # Ensure original_name is not empty
        if not original_name:
            flash('Original Book Name is required!', 'error')
            return redirect(url_for('update_book'))

        # Check if the book exists in the database
        book = db.books.find_one({'name': original_name})

        if not book:
            flash(f"Book '{original_name}' not found!", 'error')
            return redirect(url_for('update_book'))

        if delete_book:
            # Delete book from the database
            db.books.delete_one({'name': original_name})
            flash(f"Book '{original_name}' deleted successfully!", 'success')
            return redirect(url_for('update_book'))
        else:
            # Prepare update fields
            update_fields = {
                'media_type': media_type or book.get('media_type'),  # Retain original if empty
                'status': status or book.get('status'),             # Retain original if empty
                'procurement_date': procurement_date or book.get('procurement_date'),  # Retain original if empty
            }

            # Add new name to update fields only if it's not empty
            if new_name:
                update_fields['name'] = new_name
            else:
                update_fields['name'] = original_name  # Retain original name if new name is empty

            # Update the book details in the database
            db.books.update_one({'name': original_name}, {'$set': update_fields})

            flash(f"Book '{original_name}' updated successfully!", 'success')
            return redirect(url_for('update_book'))

    # Render the form for GET requests
    books = db.books.find({}, {'name': 1, '_id': 0})  # Fetch all books by name
    return render_template('update_book.html', books=list(books))




@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        # Retrieve form data
        user_type = request.form.get('userType')
        name = request.form.get('name').strip()
        password = request.form.get('password').strip()
        status = 'status' in request.form  # Checkbox for active status
        is_admin = 'admin' in request.form  # Checkbox for admin privileges

        # Debugging logs
        print(f"User Type: {user_type}, Name: {name}, Password: {password}, Status: {status}, Is Admin: {is_admin}")

        if not name or not password or not user_type:
            flash('All fields are required!', 'error')
            return redirect(url_for('add_user'))

        if user_type == 'newUser':
            existing_user = db.users.find_one({'name': name})
            if existing_user:
                flash('User already exists!', 'error')
                return redirect(url_for('add_user'))

            try:
                # Insert new user into MongoDB
                db.users.insert_one({
                    'name': name,
                    'password': password,  # Note: Use a hashed password in production
                    'status': 'active' if status else 'inactive',
                    'is_admin': is_admin
                })
                flash('User added successfully!', 'success')
            except Exception as e:
                print(f"Error: {e}")  # Debugging log
                flash(f'Error adding user: {str(e)}', 'error')
                return redirect(url_for('add_user'))

        return redirect(url_for('add_user'))

    return render_template('add_user.html')


@app.route('/update_user', methods=['GET', 'POST'])
def update_user():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username').strip()
        status = 'status' in request.form  # Checkbox for active status
        is_admin = 'admin' in request.form  # Checkbox for admin privileges
        delete_user = 'deleteUser' in request.form  # Checkbox for deleting user

        # Check if username is provided
        if not username:
            flash('Please provide a username!', 'error')
            return redirect(url_for('update_user'))

        # Find the user in the database
        user = db.users.find_one({'name': username})

        if not user:
            flash(f"User '{username}' not found!", 'error')
            return redirect(url_for('update_user'))

        if delete_user:
            # Delete user from database
            db.users.delete_one({'_id': user['_id']})
            flash(f"User '{username}' deleted successfully.", 'success')
            return redirect(url_for('update_user'))
        else:
            # Update the user's information
            db.users.update_one(
                {'_id': user['_id']},
                {'$set': {
                    'status': 'active' if status else 'inactive',
                    'is_admin': is_admin
                }}
            )
            flash(f"User '{username}' updated successfully.", 'success')
            return redirect(url_for('update_user'))

    # Render the form for GET requests
    users = db.users.find({}, {'name': 1, '_id': 0})  # Get all usernames for display
    return render_template('update_user.html', users=[user['name'] for user in users])


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Retrieve the search form data (book name)
        book_name = request.form.get('book_name', '').strip().lower()

        # MongoDB query to find matching books by book name
        query = {'name': {'$regex': book_name, '$options': 'i'}}  # Case-insensitive search for book name

        # Fetch books from MongoDB based on the query
        books = list(db.books.find(query))

        # Render the search results page with books
        return render_template('search_results.html', books=books)

    # If it's a GET request, show the search form
    return render_template('search_form.html')



@app.route('/update')
def update_page():
    return "Successfully updated!"

@app.route('/cancel')
def cancel_page():
    return render_template('cancel.html')

@app.route('/reports')
def reports():
    if 'role' in session and session['role'] == 'admin':
        # Fetch data for reports
        books = db.books.find()  # Get all books
        users = db.users.find()  # Get all users
        memberships = db.memberships.find()  # Get all memberships

        # Fetch fines details if necessary (adjust this query as per your collection structure)
        fines = db.fines.find()

        return render_template('reports.html', books=books, users=users, memberships=memberships, fines=fines)
    else:
        flash('Unauthorized access! Please log in as admin.')
        return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)
