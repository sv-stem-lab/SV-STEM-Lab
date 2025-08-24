from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.query import Query
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = 'sv.stem'

# Appwrite
client = Client()
client.set_endpoint('https://fra.cloud.appwrite.io/v1')
client.set_project('sv-stem-academy')
client.set_key(os.getenv('APPWRITE_API_KEY'))
account = Account(client)
databases = Databases(client)

@app.route("/")
def home():
    if 'email' in session:
        user_data = {}
        try:
            user_email = session.get('email')
            if user_email:
                # Fetch the user document from the 'users' collection using email query
                documents = databases.list_documents(
                    database_id='web',
                    collection_id='users',
                    queries=[Query.equal('email', user_email)]
                )
                if documents['total'] > 0:
                    user_data = documents['documents'][0]
                    session['user_id'] = user_data['$id']
                    session['type'] = user_data['type']
                    
                    # Fetch courses data based on user type
                    if user_data.get('type') in ['Developer', 'Lab Manager']:
                        # Fetch all courses data
                        courses_data = databases.list_documents(
                            database_id='web',
                            collection_id='courses'
                        )
                    elif user_data.get('type') == 'Coach':
                        # Fetch courses data for students whose names start with the coach's first letter
                        coach_firstname = user_data.get('name', '').split()[0] if user_data.get('name') else ''
                        courses_data = databases.list_documents(
                            database_id='web',
                            collection_id='courses',
                            queries=[Query.contains('coach', coach_firstname)]
                        )
                    else:
                        # For regular users, fetch only their courses
                        courses_data = databases.list_documents(
                            database_id='web',
                            collection_id='courses',
                            queries=[Query.equal('email', user_email)]
                        )
                    
                    if courses_data['total'] > 0:
                        user_data['courses'] = courses_data['documents']
                    else:
                        user_data['courses'] = []
            
        except Exception as e:
            pass

        return render_template("dashboard.html", user_data=user_data)

    return render_template("landing.html")

@app.route("/landing")
def landing():
    return render_template("landing.html")

@app.route("/sign-in", methods=['GET', 'POST'])
def sign_in():
    if 'email' in session:
        return redirect("/")
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate required fields
        if not email or not password:
            return render_template('sign-in.html', error="Email and password are required", email=email or "")
        
        try:
            user = account.create_email_password_session(
                email=email,
                password=password
            )

            session['email'] = email
            
            return redirect('/')
            
        except Exception as e:
            return render_template('sign-in.html', error=e, email=email)
    
    return render_template('sign-in.html')

@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if 'email' in session:
        return redirect("/")
    
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        name = request.form.get('name')
        
        # Validate required fields
        if not email or not password or not name:
            return render_template('sign-up.html', error="Email, password, and name are required", email=email or "", name=name or "")
        
        try:
            user = account.create(
                user_id='unique()',
                email=email,
                password=password,
                name=name
            )

            user2 = account.create_email_password_session(
                email=email,
                password=password
            )

            # Create a document for the user profile in a 'users' collection
            user3 = databases.create_document(
                database_id='web',  # Use your database ID
                collection_id='users', # Use your users collection ID
                document_id='unique()',
                data={
                    'user_id': user['$id'],
                    'email': email,
                    'name': name,
                    'phone': phone,
                }
            )

            session['email'] = email
            session['user_id'] = user3['$id']
            
            return redirect('/')

        except Exception as e:
            return render_template('sign-up.html', error=e, email=email, name=name)
    
    return render_template('sign-up.html')

@app.route("/courses", methods=['GET', 'POST'])
def courses():
    return render_template("courses.html")

@app.route("/classes", methods=['GET', 'POST'])
def classes():
    return render_template("classes.html")

@app.route("/competitions", methods=['GET', 'POST'])
def competitions():
    return render_template("competitions.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/camps")
def camps():
    return render_template("camps.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if 'email' not in session:
        return redirect("/sign-in")
        
    if request.method == 'POST':
        name = request.form.get('name')
        gender = request.form.get('gender')
        food_allergy = request.form.get('food_allergy')
        competition = request.form.get('competition')
        photo_permission = request.form.get('photo_permission')
        comments = request.form.get('comments')
        no_of_sessions = request.form.get('no_of_sessions')
        selected_classes = request.form.getlist('class')
        other_class = request.form.getlist('other_class')

        # Validate required fields
        if not name:
            return render_template("register.html", error="Name and number of sessions are required")

        try:
            if other_class == []:
                for i in selected_classes:
                    selected_class = json.loads(i)
                    info = selected_class.pop('info')
                    time = selected_class.pop('time')
                    selected_class['info'] = f"Time: {time}\nInfo: {info}"
                    selected_class['session'] = int(no_of_sessions)

                    databases.create_document(
                        database_id='web',
                        collection_id='courses',
                        document_id='unique()',
                        data={
                            'email': session.get('email'),
                            'name': name,
                            'no_of_sessions': int(no_of_sessions),
                            'gender': gender,
                            'food_allergy': food_allergy,
                            'competition': competition,
                            'photo_permission': photo_permission,
                            'comments': comments,
                            'info': info,
                            'course': selected_class['title'],
                            'time': time
                        }
                    )

                    # Get existing user document to access current schedules
                    user_id = session.get('user_id')
                    if not user_id:
                        return render_template("register.html", error="User session not found")
                    
                    user_doc = databases.get_document(
                        database_id='web',
                        collection_id='users',
                        document_id=user_id
                    )
                    
                    # Get existing schedules or initialize empty array
                    existing_schedules = user_doc.get('schedule', [])
                    
                    # Convert selected_class[0] to JSON string
                    new_schedule = json.dumps(selected_class)
                    
                    # Append new schedule
                    existing_schedules.append(new_schedule)

                    # Update the user's schedule in users collection
                    databases.update_document(
                        database_id='web',
                        collection_id='users',
                        document_id=user_id,
                        data={
                            'schedule': existing_schedules
                        }
                    )
                
            else:
                databases.create_document(
                    database_id='web',
                    collection_id='courses',
                    document_id='unique()',
                    data={
                        'email': session.get('email'),
                        'name': name,
                        'no_of_sessions': int(no_of_sessions),
                        'gender': gender,
                        'food_allergy': food_allergy,
                        'competition': competition,
                        'photo_permission': photo_permission,
                        'comments': comments,
                        'course': other_class[0]
                    }
                )
            return redirect('/')
        except Exception as e:
            return render_template("register.html", error=str(e))
    
    document = databases.get_document(
        database_id='web',
        collection_id='schedule',
        document_id='schedule'
    )
    print(document['Courses'] )
    return render_template("register.html", courses=document['Courses'])

@app.route("/logout")
def logout():
    session.pop('email', None)
    session.pop('user_id', None)
    return redirect('/')

@app.route("/calendar")
def calendar():
    if 'email' not in session:
        return redirect("/sign-in")

    email = request.args.get('email', session.get('email'))

    if email != session['email'] and session['type'] == "User":
        return render_template("pages-401.html") 
    
    try:
        documents = databases.list_documents(
            database_id='web',
            collection_id='users',
            queries=[Query.equal('email', email)]
        )
        
        user_data2 = {}
        schedules = []
        
        if documents['total'] > 0:
            user_data2 = documents['documents'][0]
            # Get schedules from user document
            schedules = user_data2.get('schedule', [])
            # Convert JSON strings back to objects
            schedules = [json.loads(schedule) for schedule in schedules]

        documents = databases.list_documents(
            database_id='web',
            collection_id='users',
            queries=[Query.equal('email', session['email'])]
        )
        
        user_data = {}
        
        if documents['total'] > 0:
            user_data = documents['documents'][0]
        
        
        return render_template("calendar.html", user_data=user_data, user_data2=user_data2, schedules=schedules)
        
    except Exception as e:
        print(f"Error in calendar route: {e}")
        return render_template("calendar.html", error=str(e))

@app.route("/save-event", methods=['POST'])
def save_event():
    if 'email' not in session and session['type'] == "User":
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        if data is None:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        userID = data.get('userID')
        events = data.get('schedule', [])
        
        event_strings = [json.dumps(event) for event in events]
        print(f"UserID: {userID}")
        print(f"Events: {event_strings}")
        
        # Update the user's schedule in users collection
        databases.update_document(
            database_id='web',
            collection_id='users',
            document_id=userID,
            data={
                'schedule': event_strings
            }
        )
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/save-form-data", methods=['POST'])
def save_form_data():
    if 'email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        if data is None:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        form_data = data.get('formData')
        
        # Save the form data to the schedule collection in Appwrite
        try:
            # Create a document in the schedule collection
            databases.update_document(
                database_id='web',
                collection_id='schedule',
                document_id='schedule',
                data={
                    'Courses': form_data,
                }
            )
            
            return jsonify({
                'success': True, 
                'message': 'Form data saved successfully'
            })
        except Exception as db_error:
            return jsonify({'error': f'Database error: {str(db_error)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('pages-404.html'), 404

if __name__ == "__main__":
    app.run(port=8000, debug=True)