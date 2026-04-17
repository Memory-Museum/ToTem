from flask import Flask, render_template, request, send_file, redirect, url_for, session, send_from_directory
from flask_qrcode import QRcode
from werkzeug.utils import secure_filename
from tinydb import TinyDB, Query
from datetime import datetime
import os
import socket

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

app = Flask(__name__)
qrcode = QRcode(app)  # Initialize QRcode extension
db = TinyDB('db.json')


# Configurations
app.secret_key = 'testTOTEM2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['QR_FOLDER'] = 'qrcodes'  # Folder to save QR code images

# Ensure the upload and QR code folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        session.clear() # Force re-registration on new visit
        
    if request.method == 'POST':
        session['firstname'] = request.form['firstname']
        session['lastname'] = request.form['lastname']
        return redirect(url_for('upload'))
    return render_template('index.html')

# Application breaks as soon as name is entered. Adding the missing upload endpoint that uploadForm.html calls to. -NH
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # Ensure user has registered (name is in session)
    if 'firstname' not in session or 'lastname' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Checking if the post request has the file part here.
        if 'file' not in request.files and 'image' not in request.files:
             # 'image' is the name in the html form
            return redirect(request.url)
        
        file = request.files.get('file') or request.files.get('image')
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # generating a unique route/ID for the user/story
            # Using timestamp 
            user_route = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Adds the other data. 
            firstname = session.get('firstname', 'Anonymous')
            lastname = session.get('lastname', '')
            title = request.form.get('title')
            description = request.form.get('description')
            mode = request.form.get('mode')
            
            db.insert({
                'route': user_route,
                'firstname': firstname,
                'lastname': lastname,
                'image_filename': filename,
                'title': title,
                'description': description,
                'mode': mode,
                'comments': []
            })
            
            return redirect(url_for('user_page', user_route=user_route))

    return render_template('uploadForm.html')




@app.route('/user/<user_route>', methods=['GET', 'POST'])
def user_page(user_route):
    User = Query()
    user_data = db.search(User.route == user_route)
    if user_data:
        user_data = user_data[0]

        # Check if mode is public
        if user_data['mode'] == 'public':
            if request.method == 'POST':
                comment_text = request.form['comment']
                
                # Gets author from session or defaults to Anonymous
                firstname = session.get('firstname', 'Anonymous')
                lastname = session.get('lastname', '')
                if firstname == 'Anonymous':
                    author = 'Anonymous'
                else:
                    author = f"{firstname} {lastname}".strip()
                
                # Creates a comment object
                comment_obj = {
                    'text': comment_text,
                    'author': author,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Stores the comment in the database TODO check over 
                current_comments = user_data.get('comments', [])
                db.update({'comments': current_comments + [comment_obj]}, User.route == user_route)

        # Generates URL for QR code. Uses LAN IP so it works for mobile scanning.
        # Generates URL for QR code. Uses LAN IP so it works for mobile scanning.
        host_ip = get_ip_address()
        qr_url = f"http://{host_ip}:5001/user/{user_route}"
        print(f"Generated URL for QR code: {qr_url}")

        # Generates QR code image
        qr_image = qrcode(qr_url, mode="raw")

        # Saves QR code image to a file
        qr_filename = f"{user_route}.png"
        qr_filepath = os.path.join(app.config['QR_FOLDER'], qr_filename)
        with open(qr_filepath, 'wb') as f:
            f.write(qr_image.getvalue())

        # Returns the URL of the saved QR code image
        qr_image_url = url_for('qr_image', filename=qr_filename)

        return render_template('user_page.html', user_data=user_data, qr_image_url=qr_image_url)

    return 'User not found', 404


@app.route('/edit/<user_route>', methods=['GET', 'POST'])
def edit_story(user_route):
    User = Query()
    user_data = db.search(User.route == user_route)
    
    if not user_data:
        return 'Story not found', 404
    
    user_data = user_data[0]

    if request.method == 'POST':
        # Prepare fields to update
        updates = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'mode': request.form.get('mode')
        }

        # Handle image update if a new file is provided
        file = request.files.get('image')
        if file and file.filename != '':
            # Delete old image if it exists
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], user_data['image_filename'])
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
            
            # Save new image
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            updates['image_filename'] = filename

        # Update database
        db.update(updates, User.route == user_route)
        
        return redirect(url_for('user_page', user_route=user_route))

    return render_template('edit_story.html', user_data=user_data, user_route=user_route)

@app.route('/delete/<user_route>', methods=['POST'])
def delete_story(user_route):
    User = Query()
    user_data = db.search(User.route == user_route)

    if user_data:
        user_data = user_data[0]
        
        # Delete image file
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], user_data['image_filename'])
        if os.path.exists(image_path):
            os.remove(image_path)

        # Delete QR code file
        qr_path = os.path.join(app.config['QR_FOLDER'], f"{user_route}.png")
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        # Remove from database
        db.remove(User.route == user_route)
        
        return redirect(url_for('gallery'))

    return 'Story not found', 404

# adding a way to see all of them -NH
@app.route('/gallery')
def gallery():
    User = Query()
    # Fetches all stories where mode is 'public'
    public_stories = db.search(User.mode == 'public')
    # Sorts by timestamp (route) descending to show newest first
    public_stories.sort(key=lambda x: x.get('route'), reverse=True)
    return render_template('gallery.html', stories=public_stories)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/qrcodes/<filename>')
def qr_image(filename):
    return send_from_directory(app.config['QR_FOLDER'], filename)

if __name__ == '__main__':
    # host='0.0.0.0' makes the server publicly available on your local network
    app.run(host='0.0.0.0', port=5001)





# Duplicated? Does not include comments. -NH
# @app.route('/user/<user_route>')
# def user_page(user_route):
#     User = Query()
#     user_data = db.search(User.route == user_route)
#     if user_data:
#         user_data = user_data[0]
        
#         # Generate URL for QR code
#         qr_url = 'http://10.16.25.118:5000/user/' + user_route
        
#         print(f"Generated URL for QR code: {qr_url}")

#         # Generate QR code image
#         qr_image = qrcode(qr_url, mode="raw")

#         # Save QR code image to a file
#         qr_filename = f"{user_route}.png"
#         qr_filepath = os.path.join(app.config['QR_FOLDER'], qr_filename)
#         with open(qr_filepath, 'wb') as f:
#             f.write(qr_image.getvalue())

#         # Return the URL of the saved QR code image
#         qr_image_url = url_for('qr_image', filename=qr_filename)

#         return render_template('user_page.html', user_data=user_data, qr_image_url=qr_image_url)

#    return 'User not found', 404