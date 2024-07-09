import configparser
import filecmp
import fileinput
from multiprocessing import connection
import os
from MySQLdb import Connect, Connection
from click import File
from db import connect
from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for , send_file
from flask_mysqldb import MySQL
import mysql.connector
from mysql.connector import Error
from werkzeug.utils import secure_filename
from flask_mail import Mail,Message 
from threading import Thread
import time


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'D:/99/files/uploaded_files'


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'memu'
#app.config["MYSQL_CURSORCLASS"] = 'DictCursor'
mysql = MySQL(app)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hariprasad26111976@gmail.com'
app.config['MAIL_PASSWORD'] = 'zrpo wosy sqby upxi'

# Initialize Flask-Mail
mail = Mail(app)






@app.route("/")
def home():
    return render_template("index.html")


@app.route('/userlogin',methods = ['GET','POST'])
def userlogin():
    if request.method == 'POST':
        ID  = request.form['ID']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE ID = %s AND password = %s", (ID, password))
        user = cur.fetchone()
        cur.close()
        
        if user:
            # If the user exists in the database, you can redirect them to a dashboard page
            return redirect(url_for('dashboard',ID = ID))
        else:
            # If the user does not exist or the password is incorrect, show an error message
            return render_template('userlogin.html', error='Invalid username or password')
    return render_template("userlogin.html")




@app.route("/dashboard/<ID>",methods=['GET', 'POST'])
def dashboard(ID):
    if request.method == 'POST':
        # Handle any form data if needed
       ID = request.form['ID']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM medidata WHERE ID = %s", (ID,))
    data = cur.fetchall()
    mysql.connection.commit()
    cur.close()

    return render_template("dashboard.html",ID = ID,data=data)


# Route for logout
@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    return redirect(url_for('userlogin'))



@app.route('/hospitallogin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        Hospitalname = request.form['Hospitalname']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM hospital WHERE Hospitalname = %s AND password = %s", (Hospitalname, password))
        user = cur.fetchone()
        cur.close()
        
        if user:
            # If the user exists in the database, you can redirect them to a dashboard page
            return redirect(url_for('medidata'))
        else:
            # If the user does not exist or the password is incorrect, show an error message
            return render_template('hospitallogin.html', error='Invalid username or password')
    return render_template('hospitallogin.html')


@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM adminlogin WHERE name = %s AND password = %s", (name, password))
        user = cur.fetchone()
        cur.close()
        
        if user:
            # If the user exists in the database, you can redirect them to a dashboard page
            return redirect(url_for('admindashboard'))
        else:
            # If the user does not exist or the password is incorrect, show an error message
            return render_template('adminlogin.html', error='Invalid username or password')
    return render_template('adminlogin.html')


@app.route('/admindashboard')
def noodles():
    return render_template("admindashboard.html")
#done



@app.route('/medidata',methods = ['GET','POST'])
def medidata():

    if request.method == 'POST':
        ID = request.form['ID']
        Date = request.form['Date']
        Hospitalname = request.form['Hospitalname']
        Complaints = request.form['Complaints']
        Diagnose = request.form['Diagnose']
        Drugprescription = request.form['Drugprescription']

        #file input
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        else:
            filename = None
        
        cur = mysql.connection.cursor()

        cur.execute(" INSERT INTO medidata (ID,Date,Hospitalname,Complaints,Diagnose,Drugprescription,filename) VALUES(%s,%s,%s,%s,%s,%s,%s)",(ID,Date,Hospitalname,Complaints,Diagnose,Drugprescription,filename))
        
        
    
        mysql.connection.commit()
        
        cur.close()
    return render_template('input_form.html') 

def new_func(file):
    filename = secure_filename(file.filename)
    return filename


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



@app.route('/signup', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        try:
            username = request.form['username']
            mobilenumber = request.form['mobilenumber']
            email = request.form['email']
            Bloodgroup = request.form['Bloodgroup']
            password = request.form['password']
            confirmpassword = request.form['confirmpassword']

            # Insert new user into the database
            insert_user(username, mobilenumber, email, password, confirmpassword)

            # Fetch the last inserted row from the database
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM users WHERE email = %s AND username = %s", (email, username))
            last_inserted_row = cur.fetchone()
            cur.close()
            


            

            if last_inserted_row:
                user_id = last_inserted_row[0]
                # Send signup email
                send_signup_email(email, username, user_id)
                return redirect(url_for('success'))  # Redirect to success page
            else:
                return 'Failed to fetch user data'  # Provide feedback to the user if data retrieval fails

        except Exception as e:
            return f'An error occurred: {str(e)}'  # Provide feedback to the user in case of errors

    return render_template("signup.html")

def insert_user(username, mobilenumber, email,Bloodgroup, password, confirmpassword):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (username, mobilenumber, email,Bloodgroup, password, confirmpassword) VALUES (%s, %s, %s, %s, %s, %s)", (username, mobilenumber, email,Bloodgroup, password, confirmpassword))
    mysql.connection.commit()
    cur.close()



#sending mail to the registerd user
def send_signup_email(email,username,user_id):
    msg = Message('Welcome to our platform!', sender='hariprasad26111976@gmail.com', recipients=[email])
    msg.body = f"Dear {username},\n\nThank you for signing up with us. Your username is {username} and your ID is {user_id}.\n\nBest regards,\nThe Team"
    mail.send(msg)


@app.route('/success')
def success():
    return 'Success! Signup email sent.'





@app.route("/hospitalregister",methods = ['GET','POST'])
def hospitalsignup():
    hospital_name = request.form['Hospitalname']
    mobilenumber = request.form['mobilenumber']
    email = request.form['email']
    address = request.form['address']
    password = request.form['passwors']

    cur = mysql.connection.cursor()

    cur.execute("INSERT INTO hospital (Hospitalname, mobilenumber, email, address, password) VALUES(%s,%s,%s,%s,%s)",(hospital_name,mobilenumber,email,address,password))
    mysql.connection.commit()
    cur.close()
    return render_template('hospitalsignup.html')






@app.route('/display')
def debug():

    cur = mysql.connection.cursor()
    # Fetch data from the database
    cur.execute("SELECT * FROM users")
    data = cur.fetchall()

    mysql.connection.commit()

    cur.close()

    # Pass the data to the template
    return render_template('display.html', data=data)




   
        


@app.route('/fetchdata',methods = ['GET','POST'])
def fetch(ID):
    if request.method == 'POST':

        ID = request.form['ID']

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM medidata WHERE ID = %s ",(ID))
        
        data = cur.fetchall()

        mysql.connection.commit()
        
        cur.close()
       
        #return render_template("medidata.html", data = data)


    return render_template("fetchdata.html", data = data)


@app.route('/testdata',methods = ['GET','POST'])
def main():
    cur = mysql.connection.cursor()
    # Fetch data from the database
    cur.execute("SELECT * FROM medidata where ID = 1123 ")

    data = cur.fetchall()

    mysql.connection.commit()

    cur.close()

    # Pass the data to the template
    return render_template('medidata.html',data = data)


@app.route('/specifieddata',methods = ['GET','POST'])
def spdmain():
    ID = None 
    if request.method == 'POST':

        ID = request.form['ID']
        print(ID)


    cur = mysql.connection.cursor()
    # Fetch data from the database
    cur.execute("SELECT * FROM medidata WHERE ID = %s ",(ID,))

    data = cur.fetchall()
    print(data)
    mysql.connection.commit()

    cur.close()

    # Pass the data to the template
    return render_template('fetchdata.html',data = data)







if __name__ == '__main__':
    app.run(debug=True)


