import pyrebase
from flask import Flask, flash, redirect, render_template, request, session, url_for
from google.cloud import datastore, storage
import secrets
from PIL import Image
import hashlib
import os
import collections

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key1.json"
app = Flask(__name__)  # Initialze flask constructor
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

firebaseConfig = {
    'apiKey': "AIzaSyDaPh65JRzUYJPXyo2CeAF9Jh568UH4cOY",
    'authDomain': "fifth-tangent-338606.firebaseapp.com",
    'projectId': "fifth-tangent-338606",
    'storageBucket': "fifth-tangent-338606.appspot.com",
    'messagingSenderId': "43587072738",
    'appId': "1:43587072738:web:f54034266a1e17b59564bb",
    'databaseURL':""

  }


# initialize firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

bucket_name = "a2k-flask-test"
client = datastore.Client()


def hash_image(file):
    md5hash2 = hashlib.md5(Image.open(file).tobytes())
    hash_code = md5hash2.hexdigest()
    return hash_code


def upload_to_bucket(blob_name, path_to_file, bucket_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(path_to_file.read(), predefined_acl="public-read")
    return blob.public_url


# Login
@app.route("/")
def login():
    try:
        if session["is_logged_in"] == True:
            return redirect(url_for('galleries'))
    except:
        return render_template("login.html")
    return render_template("login.html")


@app.route("/login")
def login_():
    try:
        if session["is_logged_in"] == True:
            return redirect(url_for('galleries'))
    except:
        return render_template("login.html")
    return render_template("login.html")


# Logout
@app.route("/logout")
def logout():
    auth.current_user = None
    session["is_logged_in"] = False
    return redirect(url_for('login'))


# Sign up/ Register
@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/result", methods=["POST", "GET"])
def result():
    if request.method == "POST":
        form_data = request.form
        email = form_data["email"]
        password = form_data["pass"]
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session["is_logged_in"] = True
            session["email"] = user["email"]
            session["uid"] = user["localId"]
            return redirect(url_for('login_'))
        except:
            message = "Email or password is incorrect please try again"
            flash(message)
            return redirect(url_for('login'))

    else:
        if session["is_logged_in"] == True:
            return redirect(url_for('galleries'))
        else:
            return redirect(url_for('login'))


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        form_data = request.form
        email = form_data["email"]
        password = form_data["pass"]
        name = form_data["name"]
        username = form_data["username"]
        query = client.query(kind="Users")
        query.add_filter('username', '=', username)
        user_info = query.fetch()
        user_list = []
        try:
            for user in user_info:
                user_list.append(user['username'])
        except:
            pass
        if username in user_list:
            message = "Username already exist please use differnt one"
            flash(message)
            return redirect(url_for('signup'))
        else:
            try:

                auth.create_user_with_email_and_password(email, password)
                # Login the user
                user = auth.sign_in_with_email_and_password(email, password)
                session["is_logged_in"] = True
                session["email"] = user["email"]
                session["uid"] = user["localId"]

                session["name"] = name
                # Append data to the firebase realtime database
                user = {"name": name, "email": email, "bio": '', "username": username,
                        'profile': ''}
                key = client.key('Users')
                item = datastore.Entity(key)
                item.update(user)
                key = client.put(item)
                return redirect(url_for('galleries'))
            except:
                message = "Email already exist please use differnt one"
                flash(message)
                return redirect(url_for('signup'))

    else:
        if session["is_logged_in"] == True:
            return redirect(url_for('galleries'))
        else:
            return redirect(url_for('register'))


# Group 2

@app.route("/galleries")
def galleries():
    if session["is_logged_in"] == True:
        email = session["email"]
        gallery_list = []
        query = client.query(kind='Gallery')
        galleries = query.fetch()
        try:
            for gallery in galleries:
                list_ = gallery['userlist']
                image_list = [0]
                if gallery['user'] == email or email in list_:
                    query = client.query(kind="Image")
                    query.add_filter('gallery', '=', str(gallery.id))
                    images = query.fetch()
                    # try:
                    total_images = 0
                    for image in images:
                        total_images += 1
                        if image['url'] is not None:
                            image_list.insert(0, {
                                'url': image['url'],
                            })
                        else:
                            image_list.append({
                                'url': "None",
                            })
                    gallery_list.append({
                        'gallery_name': gallery['gallery_name'],
                        'user': gallery['user'],
                        'id': gallery.id,
                        "image": image_list[0],
                        "total_images": total_images
                    })

        except:
            pass
        return render_template("gallary.html", gallery_list=gallery_list, email=email)
    else:
        return redirect(url_for('login'))


@app.route("/add-gallery", methods=["POST", "GET"])
def add_gallery():
    if request.method == 'POST':
        name = request.form.get('name')
        user = request.form.get('user')
        query = client.query(kind="Gallery")
        query.add_filter('gallery_name', '=', name)
        gallery_info = query.fetch()
        user_list = []
        gallery_list = []
        try:
            for gal in gallery_info:
                user_list.append(gal['user'])
                gallery_list.append(gal['gallery_name'])
        except:
            pass
        if user in user_list and name in gallery_list:
            message = "There is a gallery with the same name by this user please use different name"
            flash(message)
            return redirect(url_for('galleries'))
        data = {"user": user, "gallery_name": name, 'userlist': [0]}
        key = client.key('Gallery')
        item = datastore.Entity(key)
        item.update(data)
        key = client.put(item)
    return redirect(url_for("galleries"))


@app.route("/delete-gallery/<id>", methods=["POST", "GET"])
def delete_gallery(id):
    gallery_key = client.key("Gallery", int(id))
    query = client.query(kind="Image")
    query.add_filter('gallery', '=', id)
    images = query.fetch()
    try:
        for image in images:
            key = client.key("Image", int(image.id))
            image1 = client.get(key)
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(f"gallery_images/{image1['file_name']}")
                blob.delete()
            except:
                pass
            client.delete(key)
        client.delete(gallery_key)
    except:
        pass
    return redirect(url_for("galleries"))


@app.route("/edit-gallery", methods=["POST", "GET"])
def gallery_edit():
    user = session["email"]
    gallery_name = request.form.get('name')
    id = request.form.get('gallery_id')
    key = client.key("Gallery", int(id))
    gallery = client.get(key)

    query = client.query(kind="Gallery")
    query.add_filter('gallery_name', '=', gallery_name)
    gallery_info = query.fetch()
    user_list = []
    gallery_list = []
    try:
        for gal in gallery_info:
            user_list.append(gal['user'])
            gallery_list.append(gal['gallery_name'])
    except:
        pass
    if user in user_list and gallery_name in gallery_list:
        message = "There is a gallery with the same name by this user please use different name"
        flash(message)
        return redirect(url_for('galleries'))

    gallery["gallery_name"] = gallery_name
    client.put(gallery)
    return redirect(url_for("galleries"))


@app.route("/gallery-details/<id>", methods=["POST", "GET"])
def gallery_details(id):
    if session["is_logged_in"] == True:
        email = session["email"]
        client = datastore.Client()
        query = client.query(kind="Users")
        users = query.fetch()

        user_list = []
        for user in users:
            if user['email'] != email:
                user_list.append({
                    'email': user['email'],
                    'name': user['name'],
                })

        client = datastore.Client()
        query = client.query(kind='Gallery')
        galleries = query.fetch()
        try:
            for g in galleries:
                if int(g.id) == int(id):
                    gallery_name = g['gallery_name']
                    admin = g['user']
        except:
            pass

        image_list = []
        query = client.query(kind="Image")
        query.add_filter('gallery', '=', id)
        images = query.fetch()
        try:
            for image in images:
                image_list.append({
                    'file_name': image['file_name'],
                    'url': image['url'],
                    'gallery': image['gallery'],
                    'id': image.id
                })
        except:
            pass

        return render_template("gallery_images.html", image_list=image_list, gallery_id=id, user_list=user_list,
                                admin=admin, email=email)
    else:
        return redirect(url_for('login'))


@app.route("/add-image", methods=["POST", "GET"])
def add_image():
    if request.method == 'POST':
        blob = secrets.token_hex(3) + "-" + secrets.token_hex(3) + "-" + secrets.token_hex(3)
        file = request.files["file"]
        gallery = request.form.get('gallery')
        if file:
            _, f_ext = os.path.splitext(file.filename)
            file_name = blob + f_ext
            url = upload_to_bucket(f"gallery_images/{file_name}", file, bucket_name)
            hash_code = hash_image(file)
            data = {"file_name": file_name,
                    "gallery": gallery,
                    "userlist": [0],
                    'hash_code': hash_code,
                    "url": url}
            key = client.key('Image')
            item = datastore.Entity(key)
            item.update(data)
            key = client.put(item)
            flash("Image Added")
    return redirect(f'/gallery-details/{gallery}')


@app.route("/delete_image/<id>/<gallery_id>", methods=["POST", "GET"])
def delete_image(id, gallery_id):
    client = datastore.Client()
    gallery_key = client.key("Image", int(id))
    image = client.get(gallery_key)
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"gallery_images/{image['file_name']}")
        blob.delete()
    except:
        pass
    client.delete(gallery_key)
    return redirect(f'/gallery-details/{gallery_id}')


@app.route("/check_duplicates", methods=["POST", "GET"])
def check_duplicates():
    email = session["email"]
    query = client.query(kind="Image")
    images = query.fetch()
    list_of_hash_code = []
    image_list = []
    try:
        for image in images:
            list_of_hash_code.append(image['hash_code'])
    except:
        pass
    Dup_lis = [item for item, count in collections.Counter(list_of_hash_code).items() if count > 1]
    try:
        query = client.query(kind="Image")
        dups = query.fetch()
        for dup in dups:
            if dup['hash_code'] in Dup_lis:
                key = client.key("Gallery", int(dup['gallery']))
                gallery = client.get(key)
                if gallery['user'] == email or email in gallery['userlist']:
                    image_list.append({
                        'file_name': dup['file_name'],
                        'url': dup['url'],
                        'gallery': dup['gallery'],
                        'gallery_name': gallery['gallery_name'],
                        'hash_code': dup['hash_code'],
                        'id': dup.id
                    })
    except:
        pass

    return render_template("duplicate_images.html", image_list=image_list,
                           email=email)


@app.route("/check_duplicates_gallery/<id>", methods=["POST", "GET"])
def check_duplicates_gallery(id):
    email = session["email"]
    query = client.query(kind="Image")
    query.add_filter('gallery', '=', id)
    images = query.fetch()
    list_of_hash_code = []
    image_list = []
    try:
        for image in images:
            list_of_hash_code.append(image['hash_code'])
    except:
        pass
    Dup_lis = [item for item, count in collections.Counter(list_of_hash_code).items() if count > 1]
    try:
        query = client.query(kind="Image")
        query.add_filter('gallery', '=', id)
        dups = query.fetch()
        for dup in dups:
            if dup['hash_code'] in Dup_lis:
                key = client.key("Gallery", int(id))
                task = client.get(key)
                image_list.append({
                    'file_name': dup['file_name'],
                    'url': dup['url'],
                    'gallery': dup['gallery'],
                    'gallery_name': task['gallery_name'],
                    'hash_code': dup['hash_code'],
                    'id': dup.id
                })
    except:
        pass

    return render_template("duplicate_in_gallery.html", image_list=image_list, gallery_id=id,
                           email=email)


@app.route("/add-user-to-gallery", methods=["POST", "GET"])
def add_user_gallery():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        gallery = request.form.get('gallery')
        client = datastore.Client()
        query = client.query(kind='Gallery')
        galleries = query.fetch()
        try:
            for g in galleries:
                if int(g.id) == int(gallery):
                    list_ = g['userlist']
                    if user_name not in list_:
                        list_.append(user_name)
        except:
            pass
        key = client.key("Gallery", int(gallery))
        task = client.get(key)
        task["userlist"] = list_
        client.put(task)
    return redirect(f'/gallery-details/{gallery}')


if __name__ == "__main__":
    app.run(debug=True)
