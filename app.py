from flask import Flask, render_template, request, session, redirect, url_for,send_file, url_for, request, jsonify    
from io import BytesIO
from bson import ObjectId
import psycopg2
import pymongo
import cv2
import numpy as np

app = Flask(__name__)
app.secret_key = 'test1234'
# PostgreSQL connection
postgres_conn = psycopg2.connect(
    host="localhost",
    #host="postgres",
    port='5432',
    database='user_test',
    user='brian',
    password='Bandit2015'
)

# MongoDB connection
mongo_conn = pymongo.MongoClient('mongodb://localhost:27017/')
#mongo_conn = pymongo.MongoClient('mongodb://mongodb:27017/')

mongo_db = mongo_conn['user_test']
photos_collection = mongo_db['photos']


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get the form field values
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        # Perform the necessary operations, e.g., database insertion
        # You can use the PostgreSQL connection (postgres_conn) to interact with the database

        # Example: Insert the user data into a "users" table
        cursor = postgres_conn.cursor()
        query = "INSERT INTO users (name, email, username, password) VALUES (%s, %s, %s, %s);"
        cursor.execute(query, (name, email, username, password))
        postgres_conn.commit()
        cursor.close()

        return 'User registered successfully!'
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the form field values
        username = request.form['username']
        password = request.form['password']

               # Perform authentication logic
        cursor = postgres_conn.cursor()
        query = "SELECT * FROM users WHERE username = %s AND password = %s;"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            # Store user information in the session
            session['user_id'] = user[0]
            session['username'] = user[1]

            # Redirect to the home page
            return redirect(url_for('home'))
        else:
            return 'Invalid username or password. Please try again.'

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the user session
    session.clear()
    return redirect(url_for('index'))

@app.route('/home')
def home():
    # Get the current user from the session
    user_id = session.get('user_id')
    username = session.get('username')

    if user_id:
        # Fetch the user's photos from MongoDB using the user_id
        photos = photos_collection.find({'user_id': user_id})

        # Render the home page with the photos and current user information
        return render_template('home.html', photos=photos, username=username)
    else:
        # Redirect to the login page if the user is not logged in
        return redirect(url_for('login'))
    

@app.route('/photos/add', methods=['GET', 'POST'])
def add_photo():
    if request.method == 'POST':
        # Get the form field values
        photo_name = request.form['photo_name']
        user_id = session.get('user_id')

        # Check if a file was uploaded
        if 'photo_file' not in request.files:
            return 'No photo file provided.'

        file = request.files['photo_file']

        # Check if the file has a valid filename
        if file.filename == '':
            return 'Empty filename.'

        # Read the binary data from the file
        photo_data = file.read()

        # Clip the image using the provided coordinates
        x = int(round(float(request.form['x'])))
        y = int(round(float(request.form['y'])))
        width = int(request.form['width'])
        height = int(request.form['height'])
        print(x)
        print(y)
        width = int(request.form['width'])
        height = int(request.form['height'])

        img = cv2.imdecode(np.fromstring(photo_data, np.uint8), cv2.IMREAD_COLOR)
        clipped_img = img[y:y+height, x:x+width]

        # Convert the clipped image back to binary data
        _, clipped_data = cv2.imencode('.jpg', clipped_img)
        clipped_data = clipped_data.tobytes()

        # Insert the photo document into the collection
        photo_data = {
            'photo_name': photo_name,
            'photo_data': clipped_data,
            'user_id': user_id
        }
        photos_collection.insert_one(photo_data)

        return redirect(url_for('home'))

    return render_template('add_photo.html')

@app.route('/photos/<photo_id>')
def get_photo(photo_id):
    # Retrieve the photo from MongoDB based on the photo_id
    photo = photos_collection.find_one({'_id': ObjectId(photo_id)})

    if photo:
        # Extract the binary image data from the photo document
        image_data = photo['photo_data']

        # Create a response with the appropriate content type
        return send_file(BytesIO(image_data), mimetype='image/jpeg')
    else:
        # Handle case when photo is not found
        return 'Photo not found'

@app.route('/photos/<photo_id>/delete', methods=['POST'])
def delete_photo(photo_id):
    # Delete the photo from MongoDB based on the photo_id
    result = photos_collection.delete_one({'_id': ObjectId(photo_id)})

    if result.deleted_count > 0:
        # Photo deleted successfully
        return redirect(url_for('home'))
    else:
        # Handle case when photo is not found
        return 'Photo not found'
    

def create_users_table():
    cursor = postgres_conn.cursor()
    query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            username VARCHAR(50) NOT NULL,
            password VARCHAR(100) NOT NULL
        );
    """
    cursor.execute(query)
    postgres_conn.commit()
    cursor.close()

# Call the function to create the table
create_users_table()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)