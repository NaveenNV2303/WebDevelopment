import uuid
from flask import Flask, render_template, request, redirect, url_for
from firebase_admin import credentials, firestore, initialize_app, storage


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
    return render_template("index.html")

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
            "images": image_urls
        })

        return redirect(url_for("index"))
    except Exception as e:
        print(f"Error adding house: {e}")
        return "Error adding house", 500

# Route for listing houses
@app.route("/houses")
def list_houses():
    # Retrieve list of houses from Firestore
    houses_ref = firebase_db.collection("houses")
    houses = [doc.to_dict() for doc in houses_ref.stream()]

    return render_template("houses.html", houses=houses)

if __name__ == "__main__":
#  For Prod
#  app.run(host='0.0.0.0',port='8080', ssl_context=('cert.pem', 'privkey.pem'))
#  For Dev
 app.run(debug=True)
