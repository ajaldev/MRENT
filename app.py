import ast
import datetime
from datetime import datetime as dt
import os
from flask import Flask, jsonify,redirect,render_template,request, url_for,session,flash
import sqlite3
import json
from flask_mail import Mail, Message
from collections import defaultdict

app=Flask("__name__")
mail = Mail(app)
app.secret_key = 'mrent'


# configuration of mail 
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'bookings.mrent@gmail.com'
app.config['MAIL_PASSWORD'] = 'arew aaps bqaq iuvh'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app) 

# SQLite database setup
DATABASE = 'mrent.db'

def send(book_data):
    
    services_dict = json.loads(book_data[4])  # Assuming this is a dictionary
    services_list = [f"{key} - ₹{value}" for key, value in services_dict.items()]
    services = "<br>".join(services_list)  # Each service on a new line
   
    msgtext = f"""
    <h3>New Booking Notification</h3>
    <p>
    The user has booked a service for you. The details are:<br>
    <strong>Location:</strong> {book_data[3]}<br>
    <strong>Services:</strong> {services}<br>
    <strong>Total Value:</strong> {book_data[5]}<br>
    <strong>Date:</strong> {book_data[9]}
    </p>
    """
    print(msgtext)
    try:
        msg=Message("Booking Confirmation", sender='bookings.mrent@gmail.com', recipients=[book_data[16]])
        msg.html = msgtext
        mail.send(msg) 
    except Exception as e:
        print(f"Error occurred: {e}")

    msgtext = f"""
    <h3>New Booking Notification</h3>
    <p>
    Your Service has booked Sucessfully. The details are:<br>
    <strong>Location:</strong> {book_data[3]}<br>
    <strong>Services:</strong> {services}<br>
    <strong>Total Value:</strong> {book_data[5]}<br>
    <strong>Date:</strong> {book_data[9]}
    </p>
    """
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT email FROM customer WHERE user_id=?", (session['user_id'],))
    c_email = c.fetchone()
    print(c_email[0])
    try:
        msg=Message("Booking Confirmation", sender='bookings.mrent@gmail.com', recipients=[c_email[0]])
        msg.html = msgtext
        mail.send(msg) 
    except Exception as e:
        print(f"Error occurred: {e}")


@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if  session and session['user_id'] :
       
        if session and session['user_type']=='user':
            c.execute("SELECT users.*, customer.* FROM users JOIN customer ON users.id = customer.user_id WHERE users.id =?",(session['user_id'],))
        elif session and session['user_type']=='user':
            c.execute("SELECT users.*, mechanics.* FROM users JOIN customer ON users.id = mechanics.user_id WHERE users.id =?",(session['user_id'],))
        
        user_data=c.fetchone()
        
        return render_template('index.html',user_data=user_data)
    
    c.execute("SELECT * FROM location")
    location=c.fetchall()
    data={"location":location}
    return render_template('index.html',**data)

@app.route('/about')
def about():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM location")
    location=c.fetchall()
    data={"location":location}
    return render_template('about.html',**data)

@app.route('/contact')
def contact():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM location")
    location=c.fetchall()
    data={"location":location}
    return render_template('contact.html',**data)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'] 
        mobile = request.form['mob']
        email = request.form['email']
        location = request.form['location']
        address = request.form['address']
        password = request.form['password']
        type = request.form['type']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("INSERT INTO users (name, username, password, user_type) VALUES (?, ?, ?, ?)",
                      (name, email, password, type))
        u_id=c.lastrowid
        conn.commit()
        
        if type=='user':
            c.execute("INSERT INTO customer (name, email, mobileno, address, location, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, email, mobile, address, location,u_id))
        elif type=='mech':
            c.execute("INSERT INTO mechanics (name, email, mobile, address, location, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, email, mobile, address, location,u_id))
        
        conn.commit()
        conn.close()
        flash('Registration successful! Please log in.', 'success')

    return redirect(url_for('index'))


@app.route('/authe', methods=['GET', 'POST'])
def authe():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id, name, username, user_type FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        
        print("user:",user)
        if user:
            session['name']=user[1]
            session['user_id'] = user[0]  # Store user_id in session
            session['username'] = user[2]  # Store username in session
            session['user_type'] = user[3] # Store User Type in session
            print("usertype: ",session['user_type'])
            if session['user_type']=="admin":
                flash('Login Sucessfull', 'Sucess')
                return redirect(url_for('admin_index'))
            elif session['user_type']=="mech":
                c.execute("SELECT id FROM mechanics WHERE user_id = ?", (session['user_id'],))
                row=c.fetchone()
                session['mech_id'] = row[0]
                print(session['mech_id'])
                flash('Mechanics Login Sucessfull', 'Sucess')
                return redirect(url_for('mech_index'))
            elif session['user_type']=="user":
                flash('User Login Sucessfull', 'Sucess')
                return redirect(url_for('user_index'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return redirect(url_for('index'))


########################################
#admin Panel
########################################

@app.route('/admin_index')
def admin_index():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT count() FROM mechanics")
    session['mech']=cursor.fetchone()
    
    cursor.execute("SELECT count() FROM customer")
    session['cust']=cursor.fetchone()
    
    cursor.execute("SELECT count() FROM location")
    session['loc']=cursor.fetchone()
    
    cursor.execute("SELECT count() FROM bookings WHERE service_status='Pending'")
    session['serv']=cursor.fetchone()
    
    return render_template('admin_index.html')

@app.route('/list_mechanics')
def list_mechanics():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mechanics")
    mechanics = cursor.fetchall()
    data={"mechanics":mechanics}
    return render_template('list_mechanics.html',**data)

@app.route('/list_locations')
def list_locations():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM location")
    location = cursor.fetchall()
    data={"location":location}
    return render_template('list_locations.html',**data)

@app.route('/add_location', methods=['GET', 'POST'])
def add_location():
    return render_template('add_location.html')

@app.route('/add_location_db', methods=['GET', 'POST'])
def add_location_db():
    if request.method == 'POST':
        location = request.form['location'] 
        description = request.form['description']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("INSERT INTO location (location, description) VALUES (?, ?)",
                      (location, description))
        conn.commit()
        conn.close()
        flash('Location Added Sucessfully!', 'success')
    return redirect(url_for('list_locations'))

@app.route('/list_services', methods=['GET', 'POST'])
def list_services():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    data={"services":services}
    return render_template('list_services.html',**data)

@app.route('/add_services', methods=['GET', 'POST'])
def add_services():
    return render_template('add_services.html')

@app.route('/add_services_db', methods=['GET', 'POST'])
def add_services_db():
    if request.method == 'POST':
        service = request.form['service'] 
        description = request.form['description']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("INSERT INTO services (service, description) VALUES (?, ?)",
                      (service, description))
        conn.commit()
        conn.close()
        flash('Service Added Sucessfully!', 'success')
    return redirect(url_for('list_services'))

@app.route('/list_users', methods=['GET', 'POST'])
def list_users():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer")
    customers = cursor.fetchall()
    data={"customers":customers}
    return render_template('list_users.html',**data)

@app.route('/admin_profile', methods=['GET', 'POST'])
def admin_profile():
    return render_template('admin_profile.html')

########################################
#Mechanics Panel
########################################

@app.route('/mech_index')
def mech_index():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    
    cursor.execute("SELECT count() FROM service_assigned WHERE user_name=?",(session['user_id'],))
    services = cursor.fetchall()

    cursor.execute("SELECT count() FROM location_assigned WHERE user_name=?",(session['user_id'],))
    locations = cursor.fetchall()
    
    cursor.execute("SELECT count() FROM bookings WHERE mech_id =? and service_status=?",(session['mech_id'],"Pending"))
    booking_count = cursor.fetchall()
    
    cursor.execute("SELECT count() FROM bookings where mech_id=? and service_status!=?",(session['mech_id'],'Pending',))
    booking_count_completed = cursor.fetchall()
    
    cursor.execute("SELECT bookings.*, customer.name FROM bookings JOIN customer ON customer.user_id = bookings.customer_id WHERE bookings.mech_id =? and bookings.service_status=?",(session['mech_id'],"Pending"))
    booking_pendings = cursor.fetchall()
    print("booking_pendings:", booking_pendings)
    
    cursor.execute("SELECT * FROM bookings where mech_id=? and service_status!=?",(session['mech_id'],'Pending',))
    booking_completed = cursor.fetchall()
    
    cursor.execute("SELECT users.*, mechanics.* FROM users join mechanics on users.id= mechanics.user_id where users.id=?",(session['user_id'],))
    user_data = cursor.fetchall()
    print("user_data: ", user_data)
    mech_index_data={"user_data":user_data,"services":services,"booking_count_completed":booking_count_completed, "booking_count":booking_count, "locations":locations, "booking_pendings": booking_pendings, "booking_completed":booking_completed }
    return render_template('mech_index.html',**mech_index_data)

@app.route('/assign_services')
def assign_services():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    
    cursor.execute("SELECT * FROM service_assigned where user_name=?",(session['user_id'],))
    assservices = cursor.fetchall()
    data={'services':services, "assservices":assservices}
    return render_template('assign_services.html',**data)

@app.route('/assign_location')
def assign_location():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM location")
    locations = cursor.fetchall()
    
    cursor.execute("SELECT * FROM location_assigned where user_name=?",(session['user_id'],))
    asslocation = cursor.fetchall()
    data={'locations':locations, "asslocation":asslocation}
    return render_template('assign_location.html',**data)


def search_mech(query):
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("select la.user_name, group_concat(DISTINCT la.location) as location, m.*, GROUP_CONCAT(DISTINCT sa.service) AS services, ROUND(COALESCE(AVG(r.star_rating), 0), 1) AS avg_rating from location_assigned la JOIN mechanics m ON la.user_name=m.user_id LEFT JOIN service_assigned sa ON sa.user_name = la.user_name LEFT JOIN reviews r ON r.mech_id = m.id GROUP BY la.user_name HAVING INSTR(GROUP_CONCAT(DISTINCT la.location), ?) > 0", (query,))
    mechs = cursor.fetchall()
    #first_mech_id = mechs[0][2]
    #print(first_mech_id)
    #cursor.execute("SELECT AVG(star_rating) FROM reviews WHERE mech_id = ?", (first_mech_id,))
    #avg_rating = cursor.fetchone()[0]
    #mechs.append(avg_rating)
    print("mech:",mechs)
    
    results = mechs
   
    conn.close()
   
    return results

@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query")
    if not query:
        return jsonify([])  # Return empty response if no query
    print("Query: ",query)
    data = search_mech(query)
    print(data)
    return jsonify(data)

@app.route("/update_services",methods=["POST","GET"])
def update_services():
    if request.method == 'POST':

        service = request.form['service'] 
        amount = request.form['rate']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO service_assigned (user_name,service,amount) VALUES(?,?,?)", (session['user_id'],service,amount))
        conn.commit()
        conn.close()
        
        flash('Service Added Sucessfully!', 'success')
    return redirect(url_for('assign_services'))

@app.route("/update_location",methods=["POST","GET"])
def update_location():
    if request.method == 'POST':

        location = request.form['location'] 
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO location_assigned (location, user_name)  VALUES(?,?)", (location,session['user_id'],))
        conn.commit()
        conn.close()
        flash('Locations Added Sucessfully!', 'success')
    return redirect(url_for('assign_location'))

@app.route("/mech_profile",methods=["POST","GET"])
def mech_profile():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mechanics WHERE user_id=?",(session['user_id'],))
    mechanics = cursor.fetchone()
    return render_template('mech_profile.html',mechanics=mechanics)

@app.route("/update_mech_profile",methods=["POST","GET"])
def update_mech_profile():
    if request.method == 'POST':

        name = request.form['name'] 
        mobile = request.form['mobile']
        email=request.form['email']
        address=request.form['address']
        experiance=request.form['experiance']
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("UPDATE mechanics SET name=?, email=?, mobile=?, address=?, experiance=? WHERE user_id=?",(name, email,mobile, address,experiance, session['user_id']))
        conn.commit()
        conn.close()
        flash('Profile Updated Sucessfully!', 'success')
    return redirect(url_for('mech_profile'))


@app.route("/update_image",methods=["POST","GET"])
def update_image():
    if request.method == 'POST':

        img = request.files['img'] 
        
        image_path = os.path.join('static/uploads', img.filename)
        img.save(image_path)
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("UPDATE mechanics SET img=? WHERE user_id=?",(image_path, session['user_id']))
        conn.commit()
        conn.close()
        flash('Profile Updated Sucessfully!', 'success')
    return redirect(url_for('mech_profile'))
    
@app.route("/update_password",methods=["POST","GET"])
def update_password():
    if request.method == 'POST':
        psw=request.form['new']
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE id=?",(psw,session['user_id']))
        conn.commit()
        if session['user_type']=='admin':
            return redirect(url_for('admin_profile'))
        else:
            return redirect(url_for('mech_index'))


@app.route('/payments_recvd')
def payments_recvd():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(total_amount) FROM bookings where mech_id=? and payment_status='Paid'",(session['mech_id'],))
    t_amount = cursor.fetchone()
    print(t_amount)
    
    payments = []
    for row in cursor.execute("SELECT location, services, total_amount, date_time FROM bookings WHERE mech_id=? AND payment_status='Paid'", (session['mech_id'],)):
        location, services, total_amount, date_time_str = row
        # Convert to datetime object
        date_obj = dt.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
        formatted_date = date_obj.strftime('%d-%m-%Y')  # or '%d-%m-%y'
        payments.append((location, services, total_amount, formatted_date))
    
    data={'payments':payments,'t_amount':t_amount}
    
    return render_template('payments_recvd.html',**data)

@app.route('/status_update/<int:id>/<int:type>')
def status_update(id,type):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    if type==1:
        c.execute("UPDATE bookings SET mech_reach_time=? WHERE book_id=?",(dt.now(),id))
    elif type==2:
        c.execute("UPDATE bookings SET finished_time=?, service_status=? WHERE book_id=?",(dt.now(),"Finished",id))
    conn.commit()
    return redirect(url_for("mech_index"))




@app.route('/logout')
def logout():
    session['user_type']=""
    session['username']=""
    session['user_id']=""
    return redirect(url_for('index'))


########################################
#Mechanics Panel END
########################################

def user_data_fetch():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT users.*, customer.* FROM users JOIN customer ON users.id = customer.user_id WHERE users.id =?",(session['user_id'],))
    user_data=cursor.fetchall()
    return user_data

def history_data_fetch():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()

    cursor.execute("SELECT date_time FROM bookings WHERE customer_id=? GROUP BY date_time",(session['user_id'],))
    dates = cursor.fetchall()

    cursor.execute("SELECT b.*, m.name, m.mobile, m.email FROM bookings b JOIN mechanics m ON b.mech_id = m.id WHERE customer_id=? GROUP BY date_time",(session['user_id'],))
    book_data = cursor.fetchall()
    
    grouped_bookings = defaultdict(list)
    '''for row in book_data:
        # Extract date only (not time)
        date_only = row[9].split(" ")[0]  # Assuming row[7] is date_time
        # Safely convert service_str to dictionary
        try:
            service_dict = ast.literal_eval(row[4])
        except:
            service_dict = {}
        # Replace service_str in row with parsed dict
        processed_row = row[:5] + (service_dict,) + row[6:]
        grouped_bookings[date_only].append(processed_row)'''
        
    for row in book_data:
        row = list(row)
        try:
            row[4] = ast.literal_eval(row[4])  # safely convert service_str to dict
        except:
            row[4] = {}
        date_only = row[9].split(" ")[0]
        grouped_bookings[date_only].append(row)
        
    print("Date data:", dates)
    print("booking data:", book_data)
    print("grouped_bookings:", grouped_bookings)
    return grouped_bookings

@app.route('/user_index')
def user_index():
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM location")
    results = cursor.fetchall()
    
    cursor.execute("SELECT users.*, customer.* FROM users JOIN customer ON users.id = customer.user_id WHERE users.id =?",(session['user_id'],))
    user_data=cursor.fetchall()
    
    cursor.execute("SELECT date_time FROM bookings WHERE customer_id=? GROUP BY date_time",(session['user_id'],))
    dates = cursor.fetchall()
    
    cursor.execute("SELECT b.*, m.name, m.mobile, m.email FROM bookings b JOIN mechanics m ON b.mech_id = m.id WHERE customer_id=? GROUP BY date_time",(session['user_id'],))
    book_data = cursor.fetchall()
    
    grouped_bookings = defaultdict(list)
    '''for row in book_data:
        # Extract date only (not time)
        date_only = row[9].split(" ")[0]  # Assuming row[7] is date_time
        # Safely convert service_str to dictionary
        try:
            service_dict = ast.literal_eval(row[4])
        except:
            service_dict = {}
        # Replace service_str in row with parsed dict
        processed_row = row[:5] + (service_dict,) + row[6:]
        grouped_bookings[date_only].append(processed_row)'''
        
    for row in book_data:
        row = list(row)
        try:
            row[4] = ast.literal_eval(row[4])  # safely convert service_str to dict
        except:
            row[4] = {}
        date_only = row[9].split(" ")[0]
        grouped_bookings[date_only].append(row)
        
    print("Date data:", dates)
    print("booking data:", book_data)
    print("grouped_bookings:", grouped_bookings)
    
    data={"location":results, "user_data": user_data, "grouped_bookings": grouped_bookings}
    #print("locations:",data)
    return render_template('user_index.html',**data)

@app.route('/booking')
def booking():
    grouped_bookings=history_data_fetch()
    user_data=user_data_fetch()

    mech_userid=request.args.get('id') 
    location = request.args.get('loc')
    #print("Mech ID: ",mech_userid)
    conn = sqlite3.connect(DATABASE)  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT service,amount FROM service_assigned WHERE user_name = ?",(mech_userid,))
    row = cursor.fetchall()
    #print("service: ", row)
    if not row:
        conn.close()
        return []  # No mechanic found

    cursor.execute(f"SELECT * FROM mechanics WHERE user_id=?",(mech_userid,))
    mechanic_data = cursor.fetchone()
    
    cursor.execute("SELECT location FROM location_assigned WHERE user_name = ?",(mech_userid,))
    location_list=cursor.fetchall()
    conn.close()
    print("mechanic_data:",mechanic_data)
    #print("services_fetch: ",services)
    print("row: ",row)
    #location_list=ast.literal_eval(mechanic_data[4])
    #service_list=mechanic_data[7]
    service_data=dict(row)
    print(service_data)


    print("location_list: ", location_list)
    return render_template('booking.html',grouped_bookings=grouped_bookings,user_data=user_data,location_list=location_list,service_data=service_data,mechanic_data=mechanic_data,location=location)

@app.route("/update_user_profile",methods=["POST","GET"])
def update_user_profile():
    if request.method == 'POST':

        name = request.form['name'] 
        mobile = request.form['mobile']
        email=request.form['email']
        address=request.form['address']
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("UPDATE customer SET name=?, email=?, mobileno=?, address=? WHERE user_id=?",(name, email,mobile, address, session['user_id']))
        conn.commit()
        conn.close()
        flash('Profile Updated Sucessfully!', 'success')
    return redirect(url_for('user_index'))


@app.route('/book_service',methods=["POST","GET"])
def book_service():
    selected_services = []
    if request.method=="POST":
        mech_id=int(request.form['mech_id'])
        location=str(request.form['location'])
        selected_services=request.form.getlist('selected_services')
        print("services: ",selected_services)
        print("location: ",location)
        
        services_dict = {}

        for item in selected_services:
            key, value = item.split(":")
            services_dict[key] = int(value)
        
        print("location: ",services_dict)
        
        total=sum(services_dict.values())
        print(total)
        services_json = json.dumps(services_dict)
        
    services_str = ", ".join(services_dict) if isinstance(services_dict, list) else services_dict
    print("services_str: ",services_json)
    location_str = ", ".join(location) if isinstance(location, list) else (location or "")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    
    c.execute("INSERT INTO bookings (customer_id, mech_id, location, services, total_amount,service_status,payment_status, date_time) VALUES (?,?,?,?,?,?,?,?)",
            (session['user_id'], mech_id,location,services_json, total, "Pending","Pending",datetime.datetime.now()))
    conn.commit()
    
    c.execute("SELECT * FROM bookings")
    booking_id = c.lastrowid
    
    c.execute("SELECT b.*, m.name, m.mobile, m.email FROM bookings b JOIN mechanics m ON b.mech_id = m.id WHERE b.book_id=?",(booking_id,))
    book_data = c.fetchone()
    print(book_data)
    
    
    conn.close()
    
    send(book_data)

    grouped_bookings=history_data_fetch()
    user_data=user_data_fetch()
    
    return render_template('booking_status.html',grouped_bookings=grouped_bookings, user_data=user_data, book_data=book_data,services_offered=services_dict)

@app.route('/payment/<int:book_id>/<int:amount>')
def payment(book_id,amount):
    grouped_bookings=history_data_fetch()
    user_data=user_data_fetch()
    return render_template('payment.html',grouped_bookings=grouped_bookings, user_data=user_data, book_id=book_id,amount=amount)

@app.route('/update_pmt',methods=["POST","GET"])
def update_pmt():
    grouped_bookings=history_data_fetch()
    user_data=user_data_fetch()
    if request.method=="POST":
        book_id=int(request.form['book_id'])
        p_method=str(request.form['p_method'])
        amt=request.form['amount']
        p_details=request.form['p_details']
        pay_data= p_method+" "+p_details
        print("book_id: ", amt)
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("UPDATE bookings SET payment_status=?, pay_method=? WHERE book_id=?",("Paid",pay_data,book_id))
        conn.commit()
        conn.close()
        return render_template('pmt_status.html', grouped_bookings=grouped_bookings, user_data=user_data, book_id=book_id,amt=amt)

@app.route('/view_order/<int:book_id>',methods=["POST","GET"])
def view_order(book_id):
    grouped_bookings=history_data_fetch()
    user_data=user_data_fetch()

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("SELECT b.*, m.name, m.mobile, m.email FROM bookings b JOIN mechanics m ON b.mech_id = m.id WHERE b.book_id=?",(book_id,))
    book_data = c.fetchone()
    print(book_data)
    
    services_str=book_data[4]
    #services_str = '{"Service 1": 250}'  # your string
    services_offered = ast.literal_eval(services_str)
    print(services_offered)
    conn.close()
    
    return render_template('view_order.html',grouped_bookings=grouped_bookings, user_data=user_data,book_data=book_data,services_offered=services_offered)

@app.route('/rating/<int:book_id>',methods=["POST","GET"])
def rating(book_id):

    grouped_bookings=history_data_fetch()
    user_data=user_data_fetch()

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT b.*, m.name, m.mobile, m.email FROM bookings b JOIN mechanics m ON b.mech_id = m.id WHERE b.book_id=?",(book_id,))
    book_data = c.fetchone()
    print(book_data)
    
    services_str=book_data[4]
    #services_str = '{"Service 1": 250}'  # your string
    services_offered = ast.literal_eval(services_str)
    print(services_offered)
    conn.close()

    return render_template('add_rating.html',grouped_bookings=grouped_bookings, user_data=user_data,book_data=book_data,services_offered=services_offered)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json()
    mech_id=data['mech_id']
    rating=data['rating']
    comment=data['comment']
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    
    c.execute("INSERT INTO reviews (user_id, mech_id, star_rating, date, comment) VALUES (?,?,?,?,?)",
            (session['user_id'], mech_id,rating,datetime.datetime.now(),comment))
    conn.commit()
    
    return jsonify({'status': 'success'})

@app.route('/get_reviews/<mech_id>', methods=['GET'])
def get_reviews(mech_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT user_id, star_rating, comment, date FROM reviews WHERE mech_id = ? ORDER BY date DESC", (mech_id,))
    rows = c.fetchall()
    reviews = [{
        'user_id': row[0],
        'rating': row[1],
        'comment': row[2],
        'date': row[3]
    } for row in rows]
    return jsonify(reviews)




if __name__=="__main__":
    app.run(debug=True)
    

#/payment/
#comment
#bookings_show
#update_status
#work history