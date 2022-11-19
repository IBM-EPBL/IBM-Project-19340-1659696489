from flask import Flask, render_template, url_for, request, redirect, session, make_response , g ,flash
from flask_login import login_required, login_user, logout_user, current_user
import sqlite3 as sql
from functools import wraps
import re
import ibm_db
import os

from datetime import datetime, timedelta


conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=125f9f61-9715-46f9-9399-c8177b21803b.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=30426;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=ktx29071;PWD=zl0kavBhK4VQc9KJ", '', '')

app = Flask(__name__)
app.secret_key = 'jackiechan'

def rewrite(url):
    view_func, view_args = app.create_url_adapter(request).match(url)
    return app.view_functions[view_func](**view_args)

#----------------------------home---------------------------------------

@app.route('/', methods=['GET'])
def home():
   if session.get('loggedin')== True:
         return redirect(url_for("dashboard"))
   else:   
      return render_template('home.html')

#----------------------------logout---------------------------------------

@app.route('/logout', methods=['GET'])
def logout():
   session.pop("user",None)
   session.pop("loggedin",None)
   session.pop("registered",None)
   session.pop("uname",None)
   return redirect(url_for("home"))

#----------------------------login---------------------------------------

@app.route('/signin', methods=['GET', 'POST'])
def signin():
   lmsg = ''
   if session.get('loggedin')== True:
         return redirect(url_for('dashboard'))
   else:         
      if request.method == 'POST':
         session.pop("user",None)
         un = request.form['username']
         pd = request.form['password_1']
         print(un, pd)
         sql = "SELECT * FROM CUSTOMERS WHERE email =? AND password=?"
         stmt = ibm_db.prepare(conn, sql)
         ibm_db.bind_param(stmt, 1, un)
         ibm_db.bind_param(stmt, 2, pd)
         ibm_db.execute(stmt)
         account = ibm_db.fetch_assoc(stmt)
         print(account)
         if account:
            session['loggedin'] = True
            session['user'] = account['EMAIL']
            session['uname']=account['NAME']
            lmsg = 'Logged in successfully !'
            return redirect(url_for('dashboard')) 
         else:
            lmsg = 'Incorrect username / password !'   
            return render_template('signin.html',title="Signin",lmsg=lmsg)
      else:
         return render_template('signin.html',title="Signin")

#----------------------------dashboard---------------------------------------
           
@app.route('/dashboard' , methods=['GET', 'POST'])
def dashboard():
   if session.get('loggedin')== True:
      uname = session['uname']
      sql = 'SELECT * FROM items'
      stmt = ibm_db.exec_immediate(conn, sql)
      dictionary=ibm_db.fetch_assoc(stmt)
      items=[]
      headings = [*dictionary]
      while dictionary != False:
         items.append(dictionary)
         # print(f"The ID is : ", dictionary["NAME"])
         # print(f"The name is : ", dictionary["QUANTITY"])
         dictionary = ibm_db.fetch_assoc(stmt)
         
      return render_template('dashboard.html',title="Welcome, "+uname,headings=headings,data=items)
   else:
      return redirect(url_for("signin"))   


#-----------------------------register---------------------------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
   rmsg = ''
   if session.get('registered')==True or session.get('loggedin')==True:
      return redirect(url_for("signin"))
   else:   
      if request.method == 'POST':
         session.pop('loggedin',None)
         fname = request.form['name']
         mail = request.form['mail']
         npwd = request.form['npwd']
         cpwd = request.form['cpwd']
         check_sql = 'SELECT * FROM customers WHERE Email =?'
         stmt = ibm_db.prepare(conn, check_sql)
         ibm_db.bind_param(stmt, 1, mail)
         ibm_db.execute(stmt)
         acc_check = ibm_db.fetch_assoc(stmt)
         print(acc_check)
         if acc_check and acc_check['EMAIL']==mail:
            rmsg = 'Account already exits!!'
            return render_template('signup.html',title="Signup",rmsg=rmsg)
         elif not bool(re.match('[a-zA-Z\s]+$', fname)):
            rmsg = 'Name must contain only alphabets'
            return render_template('signup.html',title="Signup",rmsg=rmsg)   
         elif not re.match(r'[^@]+@[^@]+\.[^@]+', mail):
            rmsg = 'Enter valid email address'
            return render_template('signup.html',title="Signup",rmsg=rmsg)
         elif npwd != cpwd:
            rmsg = 'Password does not match'
            return render_template('signup.html',title="Signup",rmsg=rmsg)
         else:
            sql = "INSERT INTO customers (Name,Email,Password,Cpassword) VALUES(?,?,?,?);"
            istmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(istmt, 1, fname)
            ibm_db.bind_param(istmt, 2, mail)
            ibm_db.bind_param(istmt, 3, npwd)
            ibm_db.bind_param(istmt, 4, cpwd)
            ibm_db.execute(istmt)
            rmsg='Registeration Successful'
            session['registered'] = True
            return render_template('signin.html',title="Signin",lmsg=rmsg) 
      else:
         return render_template('signup.html',title="Signup",rmsg=rmsg)

#----------------------orders---------------------------------------
       
@app.route('/orders', methods=['GET', 'POST'])
def orders():
   if session.get('loggedin')!= True:
         return redirect(url_for("signin"))
   else:   
      return render_template('orders.html')  

#-----------------------------supplies------------------------------

@app.route('/supplies', methods=['GET', 'POST'])
def supplies():
   if session.get('loggedin')!= True:
         return redirect(url_for("signin"))
   else:   
      return render_template('supplies.html')

#-----------------------------profile------------------------------

@app.route('/profile', methods=['GET', 'POST'])
def profile():
   if session.get('loggedin')!= True:
         return redirect(url_for("signin"))
   else:   
      return render_template('profile.html')

if __name__ == '__main__':
   app.run(debug = True)

#-----------------------------editStock------------------------------

@app.route('/editstock', methods=['GET', 'POST'])
def editstock():
   if session.get('loggedin')!= True:
         return redirect(url_for("signin"))
   else:   
      return render_template('edit_stock.html')

if __name__ == '__main__':
   app.run(debug = True)   