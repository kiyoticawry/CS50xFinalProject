from cs50 import SQL
from datetime import datetime
import os
import pyotp
from flask import Flask, flash, redirect, render_template, request, session,json
from flask_session import Session
from flask import send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
#app.config["SESSION_COOKIE_NAME"] =
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

#find an API KEY
if not os.environ.get("API_KEY"): # export API_KEY="THE API KEY YOU HAVE"
    raise RuntimeError("API_KEY not set")
#flask run

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


db = SQL("sqlite:///backend.db")

@app.route("/", methods=["GET", "POST"])
def layout():
    session.clear()
    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        user = request.form.get('new username')
        password = request.form.get('new password')
        cp = request.form.get('confirm password')
        check = db.execute("SELECT COUNT(*) FROM users WHERE username = ?",user,)

        if not user or not password or not cp:
            j = {'<span>some fields are empty</span>'}
            return json.dumps(str(j)[8:-2])
        if password != cp:
            j = {'<span>the passwords dont match</span>'}
            return json.dumps(str(j)[8:-2])
        if check[0]["COUNT(*)"] >= 1:
            j = {'<span>username already exist</span>'}
            return json.dumps(str(j)[8:-2])
        else:
            hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=6)
            db.execute("INSERT INTO users(username,passwordhash) VALUES(?,?)",user,hash,)
            j = {'<span>you Registered successfully!</span>'}
            return json.dumps(str(j)[8:-2])

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        user = request.form.get('user')
        password = request.form.get('password')
        check = db.execute("SELECT * FROM users WHERE username = ?",user,)

        if len(check) != 1:
            j = {'<span>username doesnt exist</span>'}
            return json.dumps(str(j)[8:-2])
        if not check_password_hash(check[0]["passwordhash"], password):
            j = {'<span>the password is wrong</span>'}
            return json.dumps(str(j)[8:-2])
        #check sql for authbool is true
        #then put in session['key'] that key
        session["id"] = check[0]["id"]
        session["debt"] = check[0]["currentdebt"]

        idtimeline = db.execute("SELECT * FROM timeline WHERE id = ? AND status = ?",session["id"],'pending',)
        try:
            session["idtimeline"] = idtimeline[0]["idtimeline"]
        except:
                pass

        if check[0]["authkey"] == 'none':
            pass # do nothing
        else:
            session['key'] = check[0]['authkey']
            return render_template("loginauth.html")

        j = {'<span></span>'}
        return json.dumps(str(j)[8:-2])

@app.route("/loginauth", methods=["GET", "POST"])
def loginauth():
      if request.method == "POST":
        authkey = request.form.get('authkey')
        check = pyotp.TOTP(session["key"]).now()

        if not authkey:
              j = {'<span>Your authentication is empty.' + str(check) +  '</span>'}
              return json.dumps(str(j)[8:-2])
        if int(authkey) == int(check):
            j = {'<span>correct</span>'}
            return json.dumps(str(j)[8:-2])
        else:
             j = {'<span>Your authentication is wrong.</span>'}
             return json.dumps(str(j)[8:-2])

      else:
        return render_template("loginauth.html")

@app.route("/currentdebt", methods=["GET", "POST"])
@login_required
def currentdebt():
    if request.method == "POST":
        payment = request.form.get('payment')
        intervaldate = request.form.get('intervaldate')

        if not payment:
             j = {'<span>empty</span>'}
             return json.dumps(str(j)[8:-2])
        if float(payment) <= 0:
            j = {'<span>you paid nothing</span>'}
            return json.dumps(str(j)[8:-2])
        if float(payment) > session["debt"]:
            j = {'<span>youve overpaid</span>'}
            return json.dumps(str(j)[8:-2])

        def getdate():
            today = datetime.now()
            month = today.strftime("%b")
            day = today.strftime("%d")
            hour = today.strftime("%H")
            min = today.strftime("%M")
            date = month + ' ' + day + ',' + hour + ':' + min
            return date

        session["debt"] = session["debt"] - float(payment)
        db.execute("UPDATE users SET currentdebt = ?,intervaldate = ? WHERE id = ?",session["debt"],intervaldate,session["id"])
        db.execute("INSERT INTO transact (id,idtimeline,date,amountpaid) VALUES(?,?,?,?)",session["id"],session["idtimeline"],getdate(),float(payment))

        #if debt = 0 update
        if session["debt"] == 0:
            db.execute("UPDATE timeline SET status = ? WHERE id = ? AND idtimeline = ? ",'FullyPaid',session["id"],session["idtimeline"])
            db.execute("UPDATE transact SET lastpayment = ? WHERE id = ? AND idtimeline = ? AND amountpaid = ? ",'True',session["id"],session["idtimeline"],float(payment))

        j = {'<span>correct</span>'}
        return json.dumps(str(j)[8:-2])

    else:
        x = db.execute("SELECT * FROM users WHERE id = ?",session['id'])
        settingsother = db.execute("SELECT * FROM settingsother WHERE id = ?",session['id'])
        notification = x[0]['notification']
        intervals = x[0]['intervals']
        intervaldate = x[0]['intervaldate']
        debt = session["debt"]

        if not settingsother :
            db.execute("INSERT INTO settingsother (id) VALUES(?)",session['id'])
            barcolor = 'cyan'
            language = 'EN'
        else:
            barcolor = settingsother[0]['barcolor']
            language = settingsother[0]['language']

        if debt == 0:
            percentage = 0
        else:
            x = (x[0]["debt"] - x[0]["currentdebt"])/x[0]["debt"]
            percentage = int(x * 100)

        return render_template("currentdebt.html",debt=debt,percentage=percentage,barcolor=barcolor,notification=notification,intervals=intervals,intervaldate=intervaldate)

@app.route("/lendapplication", methods=["GET", "POST"])
@login_required
def lendapplication():
    if request.method == "POST":
        number = request.form.get("number")

        if number == 'none':
            j = {'<span>empty</span>'}
            return json.dumps(str(j)[8:-2])

        def addinterest(number):
            number = (int(number) * 0.03) + int(number)
            return number

        number = addinterest(number)

        def getdate():
            today = datetime.now()
            month = today.strftime("%b")
            year = today.strftime("%Y")
            day = today.strftime("%d")
            date = month + ' ' + day + ',' + year
            return date

        db.execute("UPDATE users SET currentdebt = ?,debt = ? WHERE id = ?",number,number,session["id"])
        db.execute("INSERT INTO timeline (id,datetimeline,lendamount,status) VALUES(?,?,?,?)",session["id"],getdate(),number,'pending')
        idtimeline = db.execute("SELECT * FROM timeline WHERE id = ? AND datetimeline = ? AND lendamount = ? AND status = ?",session["id"],getdate(),number,'pending')
        session["idtimeline"] = idtimeline[0]["idtimeline"]
        session["debt"] = number
        print(session["idtimeline"])

        j = {'<span>correct</span>'}
        return json.dumps(str(j)[8:-2])
    else:
        print(session['debt'])
        if session['debt'] != 0.0:
             return redirect("/currentdebt")
        else:
             return render_template("lendapplication.html")


@app.route("/newlend", methods=["GET", "POST","HEAD"])
@login_required
def newlend():
     if request.method == "POST":
        pass
     else:
        currentdebt = db.execute("SELECT * FROM users WHERE id = ?",session["id"])

        if currentdebt[0]["currentdebt"] == 0:
             j = {'<span>False</span>'}
             return json.dumps(str(j)[8:-2])
        else:
             j = {'<span>True</span>'}
             return json.dumps(str(j)[8:-2])

@app.route("/newlendPAGE", methods=["GET",])
@login_required
def newlendPAGE():
       if request.method == "GET":
            return render_template("newlend.html")



@app.route("/transactiontimeline", methods=["GET", "POST"])
@login_required
def timeline():
    if request.method == "POST":
        transactID = request.form.get("transactID")
        session["transactID"] = transactID

        j = {'<span>correct</span>'}
        return json.dumps(str(j)[8:-2])
    else:
        timeline = db.execute("SELECT * FROM timeline WHERE id = ?", session["id"])
        table = [["nothin"] * 4 for i in range(len(timeline))]
        for i in range(len(timeline)):
            table[i][0] = timeline[i]["idtimeline"]
            table[i][1] = timeline[i]["datetimeline"]
            table[i][2] = timeline[i]["lendamount"]
            table[i][3] = timeline[i]["status"]

        return render_template("transactiontimeline.html",table=table)


@app.route("/transactiontable", methods=["GET", "POST"])
@login_required
def table():
    if request.method == "POST":
        pass
    else:
        transactable = db.execute("SELECT * FROM transact WHERE id = ? AND idtimeline = ? ", session["id"],int(session["transactID"]))
        table = [["nothin"] * 3 for i in range(len(transactable))]
        for i in range(len(transactable)):
            table[i][0] = transactable [i]["date"]
            table[i][1] = transactable [i]["amountpaid"]
            table[i][2] = transactable [i]["lastpayment"]
            print(i)
        return render_template("transactiontable.html",table=table)

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        pass
    else:
        user = db.execute("SELECT * FROM users WHERE id = ?",session["id"])
        name = user[0]["username"]
        return render_template("settings.html",name=name)

@app.route("/settingsauth", methods=["GET", "POST"])
@login_required
def settingsauth():
    if request.method == "POST":
        pass
    else:
        key = pyotp.random_base32()
        qr = pyotp.totp.TOTP(key).provisioning_uri(name='justAlendingwebsite@email.com', issuer_name='securitey')
        currentqr = pyotp.TOTP(key).now()

        check = db.execute("SELECT * FROM users WHERE id  = ?",session["id"])

        if check[0]["authkey"] == 'none':
            session.pop("key", None)

        return render_template("settingsauth.html",currentqr=currentqr,qr=qr,key=key)

@app.route("/settingsauthenticate", methods=["GET", "POST"])
@login_required
def settingsauthenticate():
    if request.method == "POST":
        qr = request.form.get("qr")
        check = pyotp.TOTP(session["key"]).now()
        key = session["key"]

        if not qr:
              j = {'<span>Your authentication is empty.' + qr +  '</span>'}
              return json.dumps(str(j)[8:-2])
        if int(qr) == int(check):
            db.execute("UPDATE users SET authkey = ? WHERE id = ?",key,session['id'])
            j = {'<span>settingsauth</span>'}
            return json.dumps(str(j)[8:-2])
        else:
             j = {'<span>Your authentication is wrong.</span>'}
             return json.dumps(str(j)[8:-2])
    else:
        key = pyotp.random_base32()
        session["key"] = key
        qrcode = pyotp.totp.TOTP(key).provisioning_uri(name='justAlendingwebsite@email.com', issuer_name='securitey')
        current = pyotp.TOTP(session["key"]).now()
        return render_template("settingsauthenticate.html",key=key,qrcude=qrcode,current=current)

@app.route("/settingsauthremove", methods=["GET", "POST"])
@login_required
def settingauthremove():
    if request.method == "POST":
        password = request.form.get("Password")
        authkey = request.form.get("authkey")
        check = pyotp.TOTP(session["key"]).now()
        users = db.execute("SELECT * FROM users WHERE id = ? ",session["id"])

        if not authkey or not password:
            j = {'<span>some fields are empty/span>'}
            return json.dumps(str(j)[8:-2])
        if not check_password_hash(users[0]["passwordhash"], password):
            j = {'<span>your password is wrong</span>'}
            return json.dumps(str(j)[8:-2])
        if int(authkey) == int(check):
             db.execute("UPDATE users SET authkey = ? WHERE id = ?",'none',session['id'])
             session.pop("key", None)
             j = {'<span>settingsauth</span>'}
             return json.dumps(str(j)[8:-2])
        else:
            j = {'<span>your authentication is wrong</span>'}
            return json.dumps(str(j)[8:-2])

    else:
        return render_template("settingsauthremove.html")

@app.route("/settingsother", methods=["GET", "POST"])
@login_required
def settingsother():
    change = request.form.get('change')
    if request.method == "POST" and change == 'barcolor':

         barcolor = request.form.get('barcolor')

         db.execute("UPDATE settingsother SET barcolor = ? WHERE id = ?",barcolor,session['id'])
         j = {'<span>correct</span>'}
         return json.dumps(str(j)[8:-2])

    elif request.method == "POST" and change == 'language':

        language = request.form.get('language')

        db.execute("UPDATE settingsother SET language = ? WHERE id = ?",language,session['id'])
        j = {'<span>correct</span>'}
        return json.dumps(str(j)[8:-2])

    else:
        settingsother = db.execute("SELECT * FROM settingsother WHERE id = ?",session['id'])
        if not settingsother :
            db.execute("INSERT INTO settingsother (id) VALUES(?)",session['id'])
            barcolor = 'cyan'
            language = 'EN'
        else:
            barcolor = settingsother[0]['barcolor']
            language = settingsother[0]['language']
        return render_template("settingsother.html",barcolor=barcolor,language=language)


@app.route("/changeusername", methods=["GET", "POST"])
@login_required
def changeusername():
    if request.method == "POST":
        newn = request.form.get("New Username")
        user = db.execute("SELECT * FROM users WHERE id = ?",session["id"])

        if not newn:
            j = {'<span>its empty</span>'}
            return json.dumps(str(j)[8:-2])
        if user[0]["username"] == newn:
            j = {'<span>name not changed</span>'}
            return json.dumps(str(j)[8:-2])

        check = db.execute("SELECT COUNT(*) FROM users WHERE username = ?",newn)

        if check[0]["COUNT(*)"] >= 1:
            j = {'<span>name already exist</span>'}
            return json.dumps(str(j)[8:-2])

        db.execute("UPDATE users SET username = ? WHERE id = ?",newn,session["id"],)

        j = {'<span>youve changed your name succesfully!</span>'}
        return json.dumps(str(j)[8:-2])

    else:
        user = db.execute("SELECT * FROM users WHERE id = ?",session["id"])
        j = {'<span>' + user[0]["username"]}
        return json.dumps(str(j)[8:-2])

@app.route("/updatepassword", methods=["GET", "POST"])
@login_required
def updatepassword():
    if request.method == "POST":
        oldpass = request.form.get("Old Password")
        newpass = request.form.get("New Password")
        cp = request.form.get("Confirm Password")
        date = request.form.get("date")
        check = db.execute("SELECT * FROM users WHERE id = ?",session["id"])

        if not newpass or not cp:
            j = {'<span>some fields are empty</span>'}
            return json.dumps(str(j)[8:-2])
        if newpass != cp:
            j = {'<span>the passwords dont match</span>'}
            return json.dumps(str(j)[8:-2])
        if newpass == oldpass:
            j = {'<span>you didnt change the password at all!</span>'}
            return json.dumps(str(j)[8:-2])
        if not check_password_hash(check[0]["passwordhash"], oldpass):
            j = {'<span>your old password is wrong</span>'}
            return json.dumps(str(j)[8:-2])

        hash = generate_password_hash(cp, method="pbkdf2:sha256", salt_length=6)
        db.execute("UPDATE users SET passwordhash = ?,updatepassdate = ? WHERE id = ?",hash,date,session["id"],)
        j = {'<span>you password succesfully changed!</span>'}
        return json.dumps(str(j)[8:-2])

    else:
        users = db.execute("SELECT * FROM users WHERE id = ?",session["id"])

        if users[0]["updatepassdate"] != 'none':
            j = '<span>  ' + str(users[0]["updatepassdate"]) + 'n>'# theres a date
            return json.dumps(str(j)[8:-2])
        else:
            j = {'<span>False</span>'} # theres no date
            return json.dumps(str(j)[8:-2])

@app.route("/updatepasswordx", methods=["GET", "POST"])
@login_required
def updatepasswordx():
    if request.method == "POST":
        db.execute("UPDATE users SET updatepassdate = ? WHERE id = ?",'none',session["id"])
        j = {'<span>False</span>'}
        return json.dumps(str(j)[8:-2])

@app.route("/notification", methods=["GET", "POST","HEAD"])
@login_required
def notification():
    bool = request.form.get('bool')

    if request.method == "POST":
        if bool == 'first':

            toggle = request.form.get("toggle")

            if toggle == None:
                db.execute("UPDATE users SET notification = ? WHERE id = ?",'off',session["id"])
            else:
                db.execute("UPDATE users SET notification = ? WHERE id = ?",'on',session["id"])

            j = {'<span></span>'}
            return json.dumps(str(j)[8:-2])

        elif bool == 'second':
                selected = request.form.get("selected")

                if selected == '1 day':
                    selected = 1
                elif selected == '3 day':
                    selected = 3
                elif selected == '5 day':
                    selected = 5

                db.execute("UPDATE users SET intervals = ? WHERE id = ?", selected, session["id"])
                j = {'<span>' + str(selected) +'</span>'}
                return json.dumps(str(j)[8:-2])
    else:

        notify = db.execute("SELECT * FROM users WHERE id = ?",session['id'])
        intervals = notify[0]['intervals']

        if notify[0]["notification"] == 'on':
            toggled = notify[0]["notification"]
        else:
            toggled = None
        return render_template("notification.html",intervals=intervals,toggled=toggled)


@app.route("/deleteaccount", methods=["GET", "POST"])
@login_required
def deleteaccount():
    if request.method == "POST":
        password = request.form.get('Password')
        authentication = request.form.get('authkey')

        check = db.execute("SELECT * FROM users WHERE id = ?",session['id'])

        if check[0]['authkey'] == 'none':
            authentication = 1

        if not authentication or not password:
            j = {'<span>Some fields are empty</span>'}
            return json.dumps(str(j)[8:-2])
        elif not check_password_hash(check[0]["passwordhash"], password):
            j = {'<span>your password is wrong</span>'}
            return json.dumps(str(j)[8:-2])

        try:
            if int(authentication) != int(pyotp.TOTP(session["key"]).now()):
                j = {'<span>your authentication is wrong</span>'}
                return json.dumps(str(j)[8:-2])
        except:
                if authentication != 1:
                    j = {'<span>your authentication is wrong</span>'}
                    return json.dumps(str(j)[8:-2])

        db.execute("DELETE FROM transact WHERE id = ?",session['id'])
        db.execute("DELETE FROM timeline WHERE id = ?",session['id'])
        db.execute("DELETE FROM settingsother WHERE id = ?",session['id'])
        db.execute("DELETE FROM users WHERE id = ?",session['id'])

        j = {'<span>correct</span>'}
        return json.dumps(str(j)[8:-2])
    else:
        return render_template("deleteacount.html")