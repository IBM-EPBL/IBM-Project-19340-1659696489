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
   session.pop("ord_id",None)
   session.pop("ord_item_id",None)
   session.pop("ord_quantity",None)
   session.pop("ord_item_ppq",None)
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
      user = session['user']
      sql = 'SELECT * FROM ITEMS WHERE EMAIL =?'
      stmt = ibm_db.prepare(conn, sql)
      ibm_db.bind_param(stmt, 1, user)
      ibm_db.execute(stmt)
      dictionary=ibm_db.fetch_assoc(stmt)
      # if session.get('ord_id')== True:
      #   oiqty=dictionary["ITEMSTOCK"]
      #   niqty=session['ord_quantity']
      #   new_qty= (int)(oiqty)- (int)(niqty)
      #   orpq=dictionary["ITEMRPQ"]
      #   nrpq=session['ord_item_ppq']
      #   new_rqp= (int)(orpq)- (int)(nrpq)
      #   query = 'UPDATE ITEMS SET ITEMQUANTITYSOLD=?,ITEMRPQ=?,TOTAL=? WHERE ORDERID=? AND ITEMID=? AND EMAIL=?'
      #   pstmt = ibm_db.prepare(conn, query)
      #   ibm_db.bind_param(pstmt, 1, user)
      #   ibm_db.execute(pstmt)
      items=[]
      headings = [*dictionary]
      while dictionary != False:
         items.append(dictionary)
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
    if session.get('loggedin')== True:
        uname = session['uname']
        user = session['user']
        sql = 'SELECT * FROM ORDERS WHERE EMAIL =?'
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, user)
        ibm_db.execute(stmt)
        dictionary=ibm_db.fetch_assoc(stmt)
        items=[]
        headings = [*dictionary]
        while dictionary != False:
            items.append(dictionary)
            dictionary = ibm_db.fetch_assoc(stmt)
            
        return render_template('orders.html',title=uname+'\'s orders',headings=headings,data=items)
    else:   
        return redirect(url_for("signin"))  

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
      username=session['uname']
      email=session['user']     
      return render_template('profile.html',usname=username,email=email)

#-----------------------------editStock------------------------------

@app.route('/editstock', methods=['GET', 'POST'])
def editstock():
   if session.get('loggedin')!= True:
         return redirect(url_for("signin"))
   else:   
      return render_template('edit_stock.html')

#---------------------------addItem----------------------------------

@app.route('/createitem', methods=['GET','POST'])
def createitem():
    if request.method == 'POST':
        cimsg=''
        item_id = request.form['item_id']
        email = session['user']
        query = 'SELECT * FROM ITEMS WHERE ITEMID = ? AND EMAIL = ?'
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, item_id)
        ibm_db.bind_param(stmt, 2, email)
        ibm_db.execute(stmt)
        dictionary = ibm_db.fetch_assoc(stmt)
        if bool(dictionary)==False:
            item_name=request.form['item_name'] 
            quantity = request.form['quantity'] 
            item_ppq=request.form['item_ppq']  
            iprice=(int)(quantity)* (int)(item_ppq)
            query = 'INSERT INTO ITEMS (ITEMID,ITEMNAME,ITEMSTOCK,ITEMRPQ,ITEMTOTALWORTH,EMAIL) VALUES (?,?,?,?,?,?)'
            pstmt = ibm_db.prepare(conn, query)
            ibm_db.bind_param(pstmt, 1, item_id)
            ibm_db.bind_param(pstmt, 2, item_name)
            ibm_db.bind_param(pstmt, 3, quantity)
            ibm_db.bind_param(pstmt, 4, item_ppq)
            ibm_db.bind_param(pstmt, 5, iprice)
            ibm_db.bind_param(pstmt, 6, email)
            ibm_db.execute(pstmt)
            cimsg="Item added successfully"
            return render_template('edit_stock.html',cimsg=cimsg)
                    
        else:
            cimsg="Item already Exists!!"
            return render_template('edit_stock.html',cimsg=cimsg)        
        
    else:
        return redirect(url_for('dashboard'))

#-----------------------------removeITEM------------------------------

@app.route('/removeitem', methods=['GET','POST'])
def removeitem():
    if request.method == 'POST':
        delimsg=''
        ritem = request.form['ritem']
        email = session['user']
        query = 'SELECT * FROM ITEMS WHERE ITEMID = ?'
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, ritem)
        ibm_db.execute(stmt)
        dictionary = ibm_db.fetch_assoc(stmt)
        if bool(dictionary)==True:
            query = 'DELETE FROM ITEMS WHERE ITEMID = ? AND EMAIL = ?'
            pstmt = ibm_db.prepare(conn, query)
            ibm_db.bind_param(pstmt, 1, ritem)
            ibm_db.bind_param(pstmt, 2, email)
            ibm_db.execute(pstmt)
            delimsg="Item Removed successfully"
            return render_template('edit_stock.html',delimsg=delimsg)
                    
        else:
            delimsg="Item Does Not Exists!!"
            return render_template('edit_stock.html',delimsg=delimsg)        
        
    else:
        return redirect(url_for('dashboard'))              
      
#---------------------------addOrder----------------------------------

@app.route('/createorder', methods=['GET','POST'])
def createorder():
    if request.method == 'POST':
        comsg=''
        ord_id = request.form['ord_id']
        oitem_id =request.form['oitem_id'] 
        email = session['user']
        query = 'SELECT * FROM ORDERS WHERE ORDERID = ? AND ITEMID = ? AND EMAIL = ?'
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, ord_id)
        ibm_db.bind_param(stmt, 2, oitem_id)
        ibm_db.bind_param(stmt, 3, email)
        ibm_db.execute(stmt)
        dictionary = ibm_db.fetch_assoc(stmt)
        if bool(dictionary)==False:
            ord_quantity = request.form['ord_quantity'] 
            oitem_ppq=request.form['oitem_ppq']  
            oprice=(int)(ord_quantity)* (int)(oitem_ppq)
            query = 'INSERT INTO ORDERS (ORDERID,ITEMID,ITEMQUANTITYSOLD,ITEMRPQ,TOTAL,EMAIL) VALUES (?,?,?,?,?,?)'
            pstmt = ibm_db.prepare(conn, query)
            ibm_db.bind_param(pstmt, 1, ord_id)
            ibm_db.bind_param(pstmt, 2, oitem_id)
            ibm_db.bind_param(pstmt, 3, ord_quantity)
            ibm_db.bind_param(pstmt, 4, oitem_ppq)
            ibm_db.bind_param(pstmt, 5, oprice)
            ibm_db.bind_param(pstmt, 6, email)
            ibm_db.execute(pstmt)
            session['ord_id'] = ord_id
            session['ord_item_id'] = oitem_id
            session['ord_quantity'] = ord_quantity
            session['ord_item_ppq'] = oitem_ppq
            comsg="Order created successfully"
            return render_template('orders.html',comsg=comsg)
                    
        else:
            comsg="Order already Exists!!"
            return render_template('orders.html',comsg=comsg)        
    else:
        return redirect(url_for('dashboard'))

#---------------------------updateOrder----------------------------------

@app.route('/updateorder', methods=['GET','POST'])
def updateorder():
    if request.method == 'POST':
        upomsg=''
        up_ord_id = request.form['up_ord_id']
        up_ord_item =request.form['up_ord_item'] 
        email = session['user']
        query = 'SELECT * FROM ORDERS WHERE ORDERID = ? AND ITEMID = ? AND EMAIL = ?'
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, up_ord_id)
        ibm_db.bind_param(stmt, 2, up_ord_item)
        ibm_db.bind_param(stmt, 3, email)
        ibm_db.execute(stmt)
        dictionary = ibm_db.fetch_assoc(stmt)
        if bool(dictionary)==True:
            ord_up_quantity = request.form['ord_up_quantity']
            upd_item_ppq = request.form['upd_item_ppq']   
            uoprice=(int)(ord_up_quantity)* (int)(upd_item_ppq)
            query = 'UPDATE ORDERS SET ITEMQUANTITYSOLD=?,ITEMRPQ=?,TOTAL=? WHERE ORDERID=? AND ITEMID=? AND EMAIL=?'
            pstmt = ibm_db.prepare(conn, query)
            ibm_db.bind_param(pstmt, 1, ord_up_quantity)
            ibm_db.bind_param(pstmt, 2, upd_item_ppq)
            ibm_db.bind_param(pstmt, 3, uoprice)
            ibm_db.bind_param(pstmt, 4, up_ord_id)
            ibm_db.bind_param(pstmt, 5, up_ord_item)
            ibm_db.bind_param(pstmt, 6, email)
            ibm_db.execute(pstmt)

            upomsg="Order updated successfully"
            return render_template('orders.html',upomsg=upomsg)
                    
        else:
            upomsg="Order Does Not Exists!!"
            return render_template('orders.html',upomsg=upomsg)        
    else:
        return redirect(url_for('dashboard'))

#-----------------------------removeORDER------------------------------

@app.route('/removeorder', methods=['GET','POST'])
def removeorder():
    if request.method == 'POST':
        delomsg=''
        cancel_ord = request.form['cancel_ord']
        email = session['user']
        query = 'SELECT * FROM ORDERS WHERE ORDERID = ?'
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, cancel_ord)
        ibm_db.execute(stmt)
        dictionary = ibm_db.fetch_assoc(stmt)
        if bool(dictionary)==True:
            query = 'DELETE FROM ORDERS WHERE ORDERID = ? AND EMAIL = ?'
            pstmt = ibm_db.prepare(conn, query)
            ibm_db.bind_param(pstmt, 1, cancel_ord)
            ibm_db.bind_param(pstmt, 2, email)
            ibm_db.execute(pstmt)
            delomsg="Order Cancelled successfully"
            return render_template('orders.html',delomsg=delomsg)
                    
        else:
            delomsg="Order Does Not Exists!!"
            return render_template('orders.html',delomsg=delomsg)        
        
    else:
        return redirect(url_for('dashboard'))           



if __name__ == '__main__':
   app.run(debug = True)   