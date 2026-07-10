from flask import Flask,request,render_template,session,redirect,jsonify,flash 
from flask_sqlalchemy import SQLAlchemy
from Encryption.hashing_algo import hashing_algo
import pyotp, qrcode, io, base64
from Modules.check_host_status import nmap_scan1
from datetime import datetime, UTC
from Modules.nmap_port_scan import Open_port_scan
from Modules.dir import dir_search
from Modules.screen_shot import snap_shot
from Modules.http_status import webpage_status
import threading, os, shutil , secrets
from Modules.crawler import Scraper
from Modules.subdomain import subdomain_finder

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    Id = db.Column(db.Integer,primary_key=True)
    Username = db.Column(db.String(100))
    Password = db.Column(db.String(100))
    mfa_secret = db.Column(db.String(100))
    targets = db.relationship(
            "Target",
            backref='owner',
            lazy=True,
            cascade = "all, delete-orphan"
            )
    userSettings = db.relationship(
            "UserSettings",
            backref="owner",
            uselist=False,
            cascade = "all, delete-orphan"
            )
class UserSettings(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    mfa = db.Column(db.Boolean, default=False)
    dir_wordlist = db.Column(db.String(200),default="/usr/share/dirb/wordlists/common.txt")
    subd_wordlist = db.Column(db.String(200),default="/usr/share/dirb/wordlists/common.txt")
    user_id = db.Column(
            db.Integer,
            db.ForeignKey("user.Id"),
            nullable=False
            )

class Target(db.Model):
    Id = db.Column(db.Integer,primary_key = True)
    target_name = db.Column(db.String(250))
    target_ip = db.Column(db.String(200))
    added_by = db.Column(db.String(100))
    added_on =db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(
            db.Integer,
            db.ForeignKey('user.Id'),
            nullable=False
            )
    scan = db.relationship(
            "Scan",
            backref='target',
            lazy=True,
            cascade="all, delete-orphan"
            )


class Scan(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    target_name = db.Column(db.String(200))
    scan_type = db.Column(db.String(250))
    custon_tag = db.Column(db.String(200))
    scan_progess = db.Column(db.Integer, default=0)
    scan_status = db.Column(db.String(200))
    start_time = db.Column(db.DateTime,default=datetime.utcnow)
    end_time = db.Column(db.DateTime,nullable=True)
    target_id= db.Column(
            db.Integer,
            db.ForeignKey('target.Id'),
            nullable=False
            )

    ports = db.relationship(
            'Port',
            backref='scan',
            lazy=True,
            cascade="all, delete-orphan"
            )

    dirs = db.relationship(
            'Dirs',
            backref='dir_scan',
            lazy=True,
            cascade="all, delete-orphan"
            )
    scaper = db.relationship(
            'Scaper',
            backref='scaper_scan',
            lazy = True,
            cascade="all, delete-orphan"
            )
    subdomain = db.relationship(
            "Subdomains",
            backref="subd_scan",
            lazy=True,
            cascade="all, delete-orphan"
            )

class Dirs(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200))
    path = db.Column(db.String(200))
    status = db.Column(db.Integer)
    scan_id = db.Column(
            db.Integer,
            db.ForeignKey('scan.Id'),
            nullable=False
            )


class Port(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    port_num = db.Column(db.Integer)
    protocol = db.Column(db.String(20))
    status = db.Column(db.String(30))
    service = db.Column(db.String(100))
    version = db.Column(db.String(100))
    extraInfo = db.Column(db.String(100))
    scan_id = db.Column(
            db.Integer,
            db.ForeignKey('scan.Id'),
            nullable=False
            )
class Scaper(db.Model):
    id  = db.Column(db.Integer,primary_key=True)
    url = db.Column(db.String(300))
    path = db.Column(db.String(300))
    status = db.Column(db.Integer)
    scan_id = db.Column(
            db.Integer,
            db.ForeignKey('scan.Id'),
            nullable=False
            )
class Subdomains(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    url = db.Column(db.String(200))
    status = db.Column(db.Integer)
    server = db.Column(db.String(200))
    length = db.Column(db.Integer)
    path = db.Column(db.String(200))
    scan_id = db.Column(
            db.Integer,
            db.ForeignKey('scan.Id'),
            nullable = False
            )

@app.before_request
def log_request():
    username = session.get('user','anonymous')
    app.logger.info(
            f'{request.remote_addr} |{username}||{request.method}||{request.path}|'
            )

def logs(app):
    import logging, os
    from logging.handlers import RotatingFileHandler

    os.makedirs('logs',exist_ok= True)

    normal_handler = RotatingFileHandler('logs/Normal_logs',maxBytes=10000,backupCount=3)
    normal_handler.setLevel(logging.INFO)

    warning_handler = RotatingFileHandler('logs/Warning_logs',maxBytes=10000,backupCount=3)
    warning_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s'
            )
    for handler in [normal_handler,warning_handler]:
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)




@app.route('/')
def root_page():
    return render_template("home_page.html")

@app.route('/login', methods=['GET','POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hash_pass = hashing_algo(password)

        checking = User.query.filter_by(Username=username).first()

        if checking:
            user_name = checking.Username
        else:
            user_name = 'anonymous'

        if checking and checking.Password == hash_pass:
            session['temp_user']=checking.Username
            return redirect('/verify')
        else:
            app.logger.warning(
                    f'{request.remote_addr} |{user_name}||{request.method}||{request.path}|'
                    )
            flash("Invalid Username or Password","Invalid")
        return redirect("/login")

    return render_template('login.html')

@app.route('/verify', methods=['GET','POST'])
def verify_mfa():
    if 'temp_user' not in session:
        return redirect("/")

    user_check = User.query.filter_by(Username=session.get('temp_user')).first()

    if not user_check:
        session.pop("temp_user")
        return redirect ("/")

    user_set = user_check.userSettings

    if not user_set.mfa:
        session['user'] = user_check.Username
        session.pop('temp_user')
        return redirect("/dashboard")

    if request.method == 'POST':
        mfa_code = request.form['MFA_Code']
        username = session.get('temp_user')

        if not user_check:
            return redirect('/')
        

        topt = pyotp.TOTP(user_check.mfa_secret)

        if topt.verify(mfa_code):
            session['user'] = user_check.Username
            session.pop('temp_user')
            return redirect('/dashboard')

        else:
            flash("Invalid 6 Digit code Please try again","Invalid")
            app.logger.warning(
                    f'{request.remote_addr} |{user_check.Username}||{request.method}||{request.path}|'
                    )
    return render_template('verify_mfa.html')

@app.route('/signup',methods=['GET','POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        re_write = request.form['re-write']

        if username == '' or password == '' or re_write == '':
            flash('Please enter inputs in all fields',"Invalid")
            return redirect('/signup')
        
        if len(password) < 8 and len(re_write) < 8 :
            flash("Minimum length of password should be 8", "Invalid")
            return redirect("/signup")

        if password != re_write:
            flash("password does not match","Wrong")
            return redirect('/signup')

        exiting_user = User.query.filter_by(Username=username).first()

        if exiting_user:
            flash('User already exits',"Invalid")
            return redirect('/signup')


        session['temp_user'] = username

        hashing_pass = hashing_algo(password)

        mfa_secretKey = pyotp.random_base32()

        New_user = User(Username=username,Password=hashing_pass,mfa_secret=mfa_secretKey)
        db.session.add(New_user)
        db.session.commit()

        user_set = UserSettings()
        New_user.userSettings = user_set
        db.session.commit()

        return redirect('/setup_mfa')
    return render_template('register.html')

@app.route('/setup_mfa', methods=['GET','POST'])
def setup():
    username = session.get('temp_user')
    if not username:
        return redirect('/signup')

    user_check  = User.query.filter_by(Username=username).first()

    mfa_key = user_check.mfa_secret

    totp = pyotp.TOTP(mfa_key)
    uri = totp.provisioning_uri(
            name= user_check.Username,
            issuer_name = 'CyberFramework'
            )
    img = qrcode.make(uri)
    buff = io.BytesIO()
    img.save(buff)
    buff.seek(0)
    qr_code = base64.b64encode(buff.getvalue()).decode()

    if qr_code:
        session.pop('temp_user')


    return render_template('setup_mfa.html',qrcode=qr_code)


@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    username = session.get('user')

    user = User.query.filter_by(Username=username).first()

    if not user:
        session.clear()
        return redirect('/login')

    live_count = 0
    count=0
    live_host = 0

    targets = user.targets 

    for target in user.targets:
        for scan in target.scan:
            if scan.scan_progess < 100:
                live_count += 1
            else:
                count += 1

            result = nmap_scan1(target.target_ip)

            if len(result) != 0:
                live_host += 1
                

    return render_template('dashboard.html', targets = targets,count=count, active = live_count, host=live_host)

@app.route('/Add_Target', methods=['GET','POST'])
def add_target():
    if 'user' not in session:
        return redirect('/login')

    user = User.query.filter_by(Username=session.get('user')).first()

    if not user:
        session.clear()
        return redirect("/login")

    if request.method == 'POST':
        print(request.form)
        ip=request.form['add_target']
        scan_type = request.form.get('type')
        custom_tag1 = request.form['custom-tag']

        tag = ""

        if scan_type or custom_tag1:
            if scan_type == 'extreme':
                tag = "-sC -sV -p- -A"
            elif scan_type == 'advance':
                tag = "-sC -sV -T4"
            elif custom_tag1:
                tag = custom_tag1
        else:
            pass

        print(f"tag:{tag}")

        status= nmap_scan1(ip)

        if len(status) != 0:

            user = User.query.filter_by(Username=session.get('user')).first()

            new_target = Target(target_name=ip,target_ip=status[0],added_by=session.get('user'))
            user.targets.append(new_target)
            db.session.commit()

            new_scan = Scan(target_name=status[0],scan_type=scan_type,custon_tag=tag,scan_progess=0,scan_status='starting')

            new_target.scan.append(new_scan)
            db.session.commit()

            threading.Thread(target=run_nmap_scan, args=(new_scan.Id,tag,),daemon=True).start()

            return redirect('/dashboard')
        else :
             flash("Can't Resolve Domain Name or Host might be down","Wrong")
             return redirect("/Add_Target")

    return render_template('add_target.html')

def run_nmap_scan(scan_id,tag):
    
    with app.app_context():
        scan = Scan.query.get(scan_id)
        ip = scan.target.target_ip
        arg = tag
        results = Open_port_scan(ip,arg)

        for result in results:
            new_port= Port(port_num=result['port'],protocol=result['protocol'],status=result['status'],service=result['service'], version = result['version'], extraInfo = result['extrainfo'])
            scan.ports.append(new_port)
        db.session.commit()
        scan.scan_progess = 25
        scan.scan_status="Running"
        db.session.commit()
        directories(scan_id)

def directories(scan_id):

    with app.app_context():
        scan = Scan.query.get(scan_id)
        name = scan.target.owner.Username
        user = scan.target.owner

        wordlist = user.userSettings.dir_wordlist

        ip= scan.target.target_name
        ip_addr = []
        for port in scan.ports:
            url = f'{ip}:{port.port_num}'
            http,https = webpage_status(url)
            if http or https:
                ip_addr.append(url)
            for addr in ip_addr:
                results = dir_search(name,addr,wordlist)

                for page in results:
                    new_dir = Dirs(url=page['url'],path=page['file_path'],status=page['status code'])
                    scan.dirs.append(new_dir)
                db.session.commit()
        scan.scan_progess = 50
        db.session.commit()
        web_scraper(name,ip_addr,scan_id)

def web_scraper(name,ip_addr,scan_id):

    with app.app_context():
        scan  = Scan.query.get(scan_id)

        for target in ip_addr:
            result = Scraper(name,target)

            for link in result:
                new_dir = Scaper(url=link['url'],path=link['path'],status=link['status code'])
                scan.scaper.append(new_dir)
        db.session.commit()
        scan.scan_progess = 75
        scan.scan_status = "Running"
        db.session.commit()
        subdomain(name,ip_addr,scan_id)

def subdomain(name,ip_addr,scan_id):
    with app.app_context():

        scan  = Scan.query.get(scan_id)
        user = scan.target.owner

        wordlist = user.userSettings.subd_wordlist

        for target in ip_addr:
            result = subdomain_finder(name,target,wordlist)

            for link in result:
                new_subd = Subdomains(url=link['url'],status=link['status'],server=link['server'],length=link['length'],path=link['path'])
                scan.subdomain.append(new_subd)
        db.session.commit()
        scan.scan_progess = 100
        scan.scan_status = "Completed"
        scan.end_time = datetime.utcnow()
        db.session.commit()

@app.route('/Scan_History', methods=['GET','POST'])
def Scan_history():
    if 'user' not in session:
        return redirect('/login')

    username  = session.get('user')

    user = User.query.filter_by(Username=username).first()

    if not user:
        session.clear()
        return redirect('/login')

    search = request.args.get("Search","").strip()

    if search:
        scan_history = Target.query.filter(Target.added_by==username, Target.target_name.ilike(f"%{search}%")).all()

        if not scan_history:
            flash("Target Not Found","Invalid")
            return redirect('/Scan_History')
    
    else:
        scan_history = Target.query.filter_by(added_by=username).all()

    return render_template('Scan_history.html',targets=scan_history)
@app.route('/active_scans', methods=['GET','POST'])
def Active_scan():
    if 'user' not in session:
        return redirect('/login')

    username = session.get('user')

    user = User.query.filter_by(Username=username).first()

    if not user:
        session.clear()
        return redirect('/login')

    result = []

    for target in user.targets:
        for scan in target.scan:
            if scan.scan_progess < 100:
                result.append(target)

    if request.method == 'POST':

        for target in user.targets:
            for scan in target.scan:
                if scan.scan_progess < 33:
                    threading.Thread(target=run_nmap_scan, args=(scan.Id,scan.custon_tag,),daemon=True).start()
                elif scan.scan_progess >= 33 and scan.scan_progess <= 66 :
                    threading.Thread(target=directories, args=(scan.Id,), daemon=True).start()
                else:
                    continue

    return render_template('active_scan.html', targets=result)


@app.route('/api/scans')
def scans_status():

    if 'user' not in session:
        return redirect('/login')

    user = User.query.filter_by(Username=session.get('user')).first()

    if not user:
        session.clear()
        return redirect('/login')

    data = []
    for target in user.targets:
        for scans in target.scan:

            elapsed = 0 

            if scans.end_time:

                elapsed = int((scans.end_time - scans.start_time).total_seconds())
            else:
                elapsed = int((datetime.utcnow() - scans.start_time).total_seconds())

            data.append({
                "id": scans.Id,
                "progress": scans.scan_progess,
                "scan_status":scans.scan_status,
                "elapsed":elapsed,
                "time":scans.start_time.isoformat() + "Z"
                })
    return jsonify(data)

@app.route('/total_scan_history')
def history():
    if 'user' not in session:
        return redirect('/login')

    user = User.query.filter_by(Username=session.get('user')).first()

    if not user:
        session.clear()
        return redirect('/login')

    result = []
    for target in user.targets:
        for scan in target.scan:
            if scan.scan_progess == 100:
                result.append({
                    "name":target.target_name,
                    "id": scan.Id
                    })

    return render_template('history.html', targets = result)

@app.route('/nmap_result/<int:scan_id>')
def nmap_history(scan_id):
    if 'user' not in session:   
        return redirect('/login')

    scan = (Scan.query.join(Target).join(User).filter(Scan.Id == scan_id, User.Username == session.get('user')).first_or_404())


    return render_template('nmap_history.html', scan = scan)

@app.route('/dir/<int:scan_id>')
def dir_result(scan_id):
    if 'user' not in session:
        return redirect('/login')

    scan = (Scan.query.join(Target).join(User).filter(Scan.Id==scan_id,User.Username==session.get('user')).first_or_404())

    dir_screenshot = 0

    if scan:
        dir_screenshot += sum(1 for d in scan.dirs if d.path)

    scan.dirs.sort(
            key=lambda d: d.path == ""
            )


    return render_template('dir.html', scan=scan, screenshots = dir_screenshot)

@app.route('/scraper/<int:scan_id>')
def scraper_webpage(scan_id):
    if 'user' not in session:
        return redirect('/login')

    scan = (Scan.query.join(Target).join(User).filter(Scan.Id==scan_id,User.Username==session.get('user')).first_or_404())

    screenshot = 0

    if scan:

        screenshot += sum(1 for d in scan.scaper if d.path)


    return render_template('scraper.html',scan=scan, screenshots=screenshot)

@app.route("/Subdomain/<int:scan_id>")
def subd(scan_id):
    if 'user' not in session:
        return redirect("/login")
    
    scan = (Scan.query.join(Target).join(User).filter(Scan.Id==scan_id,User.Username==session.get('user')).first_or_404())

    if not scan:
        return redirect("/login")
    
    servers = []
    lenght = []
    
    for subd in scan.subdomain:
        servers.append(subd.server)
        lenght.append(subd.length)

            
    return render_template("subdomain.html",scan=scan,servers=servers,lengths=lenght)

@app.route('/delete/<int:scan_id>')
def delete_scan(scan_id):
    if 'user' not in session:
        return redirect('/login')

    target = Target.query.filter_by(Id=scan_id).first()

    if target:

        for scan in target.scan:

            for port in scan.ports:

                file1 =f"static/screenshot/{session.get('user')}_{target.target_name}:{port.port_num}"
                file2 = f"static/webpage_screenshot/{session.get('user')}_{target.target_name}:{port.port_num}"
                file3  = f"static/subdomain/{session.get('user')}_{target.target_name}:{port.port_num}"

                for files in [file1,file2,file3]:
                    if os.path.exists(files):
                        shutil.rmtree(files)
                        return redirect("/total_scan_history")

        db.session.delete(target)
        db.session.commit()
    return redirect("/total_scan_history")

@app.route('/api/nmap_result')
def nmap_details():
    if 'user' not in session:
        return redirect('/login')

    user = User.query.filter_by(Username=session.get('user')).first()

    if not user:
        session.clear()
        return redirect('/login')

    return jsonify(user)

@app.route('/live_host')
def live_hosts():
    if 'user' not in session:
        return redirect("/login")

    user = User.query.filter_by(Username=session.get('user')).first()

    if not user:
        return redirect("/login")

    targets = []

    for target in user.targets:
        result = nmap_scan1(target.target_name)

        if len(result) != 0:
            targets.append(target)

    return render_template("live_host.html", targets=targets)
@app.route('/Settings', methods=['GET','POST'])
def UserSetting():

    if 'user' not in session:
        return redirect('/login')

    user = User.query.filter_by(Username=session.get('user')).first()

    user_set = user.userSettings

    dir_count = 0
    scraper_count = 0
    total_target = len(user.targets)

    for target in user.targets:
        for scan in target.scan:
            if scan:
                dir_count += sum(1 for d in scan.dirs if d.path)
                scraper_count +=sum(1 for s in scan.scaper if s.path)
    total_screenshot = dir_count + scraper_count

    if not user:
        return redirect('/login')

    if request.method == "POST":
        old_pwd = request.form['old-password']
        new_pwd = request.form['new-password']
        again_pwd = request.form['new1-password']

        current_pwd = hashing_algo(old_pwd)

        if not current_pwd:
            return redirect('/Settings')

        if current_pwd != user.Password:
            flash("Invalid password", "Wrong")
            return redirect('/Settings')

        if new_pwd != again_pwd:
            flash("New Password and Confirm password doesn't match","Invalid")
            return redirect('/Settings')

        user.Password = hashing_algo(new_pwd)
        db.session.commit()
        flash('Successfully  Changed Password','Success')

        return redirect('/Settings')

    return render_template('UserSetting.html', user = user_set,screenshot=total_screenshot, total_target=total_target)

@app.route("/change_mfa", methods=['POST'])
def MFA_settings():
    if 'user' not in session:
        return redirect("/login")

    user = User.query.filter_by(Username=session.get('user')).first()

    if not user:
        session.clear()
        return redirect("/login")

    if request.method == "POST":

        user_set = user.userSettings
        user_set.mfa = (
                "mfa-enable" in request.form
                )

        db.session.commit()

        if user_set.mfa:
            flash("MFA Setting Updated","Success")
        else:
            flash("MFA Disable", "Invalid")

    return redirect("/Settings")

@app.route("/wordlist_setting", methods=["POST"])
def wordlist():
    if 'user' not in session:
        return redirect("/login")

    user = User.query.filter_by(Username=session.get("user")).first()

    if not user:
        session.clear()
        return redirect("/login")

    if request.method == "POST":
        dir_wordlist = request.form.get('dir_wordlist',"")
        subd_wordlist = request.form.get('subd_wordlist',"")
  
        user_set = user.userSettings
        if not user_set:
            flash("User settings not found","Invalid")
            return redirect("/Settings")

        if dir_wordlist:
            if os.path.isfile(dir_wordlist) and os.access(dir_wordlist, os.R_OK):
                user_set.dir_wordlist = dir_wordlist
            else:
                flash("Directory wordlist missing or access denied","Invalid")
                return redirect("/Settings")
        if subd_wordlist:
            if os.path.isfile(subd_wordlist) and os.access(subd_wordlist, os.R_OK):
                user_set.subd_wordlist = subd_wordlist
            else:
                flash("Subdomain wordlist missing or access denied","Invalid")
                return redirect("/Settings")
        
        db.session.commit()

        flash("Wordlist Updated Succesfully","Success")

        return redirect("/Settings")

    return redirect("/Settings")


@app.route("/delete_screenshots", methods=["POST"])
def Delete_screenshot():
    if 'user' not in session:
        return redirect("/login")

    user = User.query.filter_by(Username=session.get('user')).first()

    if not user:
        return redirect("/login")

    if request.method == "POST":

        deleted = False

        for target in user.targets:
            for scan in target.scan:
                for port in scan.ports:
                    file1 =f"static/screenshot/{session.get('user')}_{target.target_name}:{port.port_num}"
                    file2 = f"static/webpage_screenshot/{session.get('user')}_{target.target_name}:{port.port_num}"
                    file3 = f"static/subdomain/{session.get('user')}_{target.target_name}:{port.port_num}"
                    for dirs in scan.dirs:
                        dirs.path = ""
                    for page in scan.scaper:
                        page.path = ""
                    db.session.commit()
                    for files in [file1,file2,file3]:
                        if os.path.exists(files):
                            shutil.rmtree(files)
                            deleted = True
                            return redirect("/Settings")

        if deleted:
            flash("All Screenshots Deleted Successfully","Success")
        else:
            flash("No Screenshot Found To Delete","Invalid")

    return redirect("/Settings")
            
@app.route('/logout')
def logout():
    if 'user' not in session:
        return redirect('/login')
    session.pop('user')
    return redirect('/login')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    logs(app)
    app.run(host='0.0.0.0',port=5000,debug=False)
