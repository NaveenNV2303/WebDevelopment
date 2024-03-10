from functools import wraps
import uuid
from flask import Flask, render_template, request, redirect, session, url_for
from firebase_admin import credentials, firestore, initialize_app, storage, auth


app = Flask(__name__)
app.secret_key = "secrecetKeyForWebApplication"

# Firebase configuration
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_app = initialize_app(cred, {
        'storageBucket': 'webdevelopment-f2d20.appspot.com'
    })
    firebase_db = firestore.client()
    storage_client = storage.bucket()   
except Exception as e:
    print(f"Error initializing Firebase: {e}")


# Default landing page for the website.
@app.route("/")
def index():
    if 'user' in session and session['user'] == 'admin@gmail.com':
        return render_template("admin_dashboard.html")
    # Retrieve list of houses from Firestore
    return render_template("homePageForCustomer.html")

# Add House to firebase
@app.route("/add_house", methods=["POST"])
def add_house():
    try:
    # Get form data
        address = request.form["address"]
        location = request.form["location"]
        description = request.form["description"]
        price = float(request.form["price"])
        facilities = request.form["facilities"]
        bedroom = request.form["bedroom"]
        bathroom = request.form["bathroom"]
        phoneNumber = request.form["phoneNumber"]
        images = request.files.getlist("images")
        image_urls = []

        # Upload images to Firebase Storage
        for image in images:
            if image.filename != "":
                # generate id and making path
                folder_name = str(uuid.uuid4())
                # Upload image to Firebase Storage
                image_blob = storage_client.blob(f"{folder_name}/{image.filename}")
                image_blob.upload_from_file(image)

                # Get the public URL of the uploaded image
                image_blob.make_public()
                image_url = image_blob.public_url
                print("image_url:",image_url)
                image_urls.append(image_url)

        # Add house details to Firestore
        house_ref = firebase_db.collection("houses").add({
            "address": address,
            "location": location,
            "description": description,
            "price": price,
            "facilities": facilities,
            "bedroom":bedroom,
            "bathroom":bathroom,
            "phoneNumber":phoneNumber,
            "images": image_urls
        })

        return redirect(url_for("admin_dashboard"))
    except Exception as e:
        print(f"Error adding house: {e}")
        return "Error adding house", 500


# update House to firebase
@app.route("/update_house", methods=["POST"])
def update_house():
    try:
        # Get house data from the request
        house_id = request.form.get("house_id")
        address = request.form.get("address")
        location = request.form.get("location")
        description = request.form.get("description")
        price = float(request.form.get("price"))
        facilities = request.form.get("facilities")
        bedroom = request.form["bedroom"]
        bathroom = request.form["bathroom"]
        phoneNumber = request.form["phoneNumber"]

        # Update house details in Firestore
        house_ref = firebase_db.collection("houses").document(house_id)
        house_ref.update({
            "address": address,
            "location": location,
            "description": description,
            "price": price,
            "facilities": facilities,
            "bedroom":bedroom,
            "bathroom":bathroom,
            "phoneNumber":phoneNumber
        })

        return redirect(url_for("admin_dashboard"))
    except Exception as e:
        print(f"Error updating house: {e}")
        return "Error updating house", 500
    
# Delete House to firebase
@app.route("/delete_house/<house_id>", methods=["DELETE","GET"])
def delete_house(house_id):
    try:
        # delete house details in Firestore
        firebase_db.collection("houses").document(house_id).delete()
        houses_ref = firebase_db.collection("houses")
        houses = []
        for doc in houses_ref.stream():
            house_data = doc.to_dict()
            house_data["id"] = doc.id
            houses.append(house_data)
        return render_template('admin_dashboard.html', houses=houses)
    except Exception as e:
        print(f"Error updating house: {e}")
        return "Error updating house", 500
    
# Route for listing houses
@app.route("/home")
def list_houses():
    houses_ref = firebase_db.collection("houses")
    houses = []
    for doc in houses_ref.stream():
        house_data = doc.to_dict()
        house_data["id"] = doc.id
        houses.append(house_data)
    if 'user' in session and session['user'] == 'admin@gmail.com':
        return render_template("admin_dashboard.html", houses=houses)
    # Retrieve list of houses from Firestore
    return render_template("homePageForCustomer.html", houses=houses)

# Route for about page
@app.route("/about")
def aboutPage():
    return render_template("about.html")

# Route for services page
@app.route("/services")
def servicesPage():
    return render_template("services.html")

# Route for contact page
@app.route("/contact")
def contactPage():
    return render_template("contact.html")

# This function checks if the user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_admin_credentials(username, password):
            session['user'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Protected route accessible only when logged in
@app.route('/admin')
@login_required
def admin_dashboard():
    houses_ref = firebase_db.collection("houses")
    houses = []
    for doc in houses_ref.stream():
        house_data = doc.to_dict()
        house_data["id"] = doc.id
        houses.append(house_data)
    return render_template('admin_dashboard.html', houses=houses)

# Function to verify admin credentials
def verify_admin_credentials(email, password):
    try:
        # Sign in with email and password
        user = auth.get_user_by_email(email)
        print('user details ', format(user))
        return True
    except ValueError as e:
        print(f"Authentication error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
#  For Prod
#  app.run(host='0.0.0.0',port='8080', ssl_context=('cert.pem', 'privkey.pem'))
#  For Dev
 app.run(debug=True)
