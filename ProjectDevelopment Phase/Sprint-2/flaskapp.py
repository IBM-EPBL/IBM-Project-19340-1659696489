from flask import Flask, render_template, url_for, request, redirect, session, make_response
import sqlite3 as sql
from functools import wraps
import re
import ibm_db
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime, timedelta


conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=125f9f61-9715-46f9-9399-c8177b21803b.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=30426;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=ktx29071;PWD=zl0kavBhK4VQc9KJ", '', '')

app = Flask(__name__)
app.secret_key = 'jackiechan'

def rewrite(url):
    view_func, view_args = app.create_url_adapter(request).match(url)
    return app.view_functions[view_func](**view_args)

@app.route('/', methods=['GET'])
def home():
   return render_template('home.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
   global userid
   msg = ''

   if request.method == 'POST':
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
         session['id'] = account['EMAIL']
         userid = account['NAME']
         msg = 'Logged in successfully !'
         return render_template('index.html',msg=msg)
      else:
         msg = 'Incorrect username / password !'
   return render_template('signin.html',msg=msg)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
   if request.method == 'POST':
      fname = request.form['name']
      mail = request.form['mail']
      npwd = request.form['npwd']
      cpwd = request.form['cpwd']
      if npwd != cpwd:
         return render_template('signup.html')

      sql = "INSERT INTO customers (Name,Email,Password,Cpassword) VALUES(?,?,?,?);"
      stmt = ibm_db.prepare(conn, sql)
      ibm_db.bind_param(stmt, 1, fname)
      ibm_db.bind_param(stmt, 2, mail)
      ibm_db.bind_param(stmt, 3, npwd)
      ibm_db.bind_param(stmt, 4, cpwd)
      ibm_db.execute(stmt)
      return render_template('signin.html')
   return render_template('signup.html')
   

if __name__ == '__main__':
   app.run(debug = True)