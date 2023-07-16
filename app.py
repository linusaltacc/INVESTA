from flask import Flask, render_template, request, redirect, render_template_string
from flask import session, g
import os 
import bcrypt
from models import db
from palm import handle_chat
import ast
app = Flask(__name__)
app.secret_key=os.urandom(24)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        result = request.form
        username = result['username']
        name = result["name"]
        email = result["email"]
        password = result["password"].encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt(8))
        role = result['role']
        if role == 'investor':
            data = db.collection('investors').document(username)
            if not data.get().exists:
                data.set({'name':name, 'Email':email, 'hashed_password':hashed, 'role':'investor'})
                return render_template('investor/app.html')
            else:
                return render_template_string("Investor already exists. please sign in")
        elif role == 'innovator':
            data = db.collection('innovators').document(username)
            if not data.get().exists:
                data.set({'name':name, 'Email':email, 'hashed_password':hashed, 'role':'innovator'})
                return redirect('/dashboard/portfolio')
            else:
                return render_template_string("innovator already exists. please sign in")
        elif role == 'mentor':
            data = db.collection('mentors').document(username)
            if not data.get().exists:
                data.set({'name':name, 'Email':email, 'hashed_password':hashed, 'role':'mentor'})
                return render_template('mentor/app.html')
            else:
                return render_template_string("mentor already exists. please sign in")        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        result = request.form
        username = result['username']
        password = result['password']
        role = result['role']
        if role == 'investor':
            data = db.collection('investors').document(username)
            if data.get().exists:
                data = data.get().to_dict()
                if bcrypt.checkpw(password.encode('utf-8'), data['hashed_password']):
                    # session['username'] = username
                    session['investor'] = username
                    return redirect("/dashboard")
                else:
                    return render_template_string("Wrong password")
            else:   
                return "User does not exist"
        elif role == 'innovator':
            data = db.collection('innovators').document(username)
            if data.get().exists:
                data = data.get().to_dict()
                if bcrypt.checkpw(password.encode('utf-8'), data['hashed_password']):
                    # session['username'] = username
                    session['innovator'] = username
                    return redirect("/dashboard")
                else:
                    return render_template_string("Wrong password")
            else:   
                return "User does not exist"
        elif username == 'mentor':
            data = db.collection('mentor').document(username)
            if data.get().exists:
                data = data.get().to_dict()
                if bcrypt.checkpw(password.encode('utf-8'), data['hashed_password']):
                    # session['username'] = username
                    session['mentor'] = username
                    return render_template("mentor/app.html")
                else:
                    return render_template_string("Wrong password")
            else:   
                return "User does not exist"  
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if g.innovator:
        data = get_growth(g.innovator)
        ai_pred = handle_chat("with the following context:"+ str(data) + """replay with forcast of next year sales only from apr to dec with values and keys as string. only reply with dictionry.""")
        ai_pred = ast.literal_eval(ai_pred)
        print(ai_pred)
        get_port = get_portfolio(g.innovator)
        ai_sug = handle_chat("with the following context of the startup:"+ str(get_port['one_liner'])+ """replay with suggestions for the investor regarding the growth of the company in the form of a chatbot.""")
        return render_template("innovator/dashboard.html", ap=data['avg_profit'] ,du=data['daily_users'],
        nc=data['new_clients'], s=data['sales'], u=data['users'], c=data['clicks'], asl=data['active_sales'], i=data['items'], inc=data['inc'], y=data['year'], apr=data['Apr'], may=data['May'], jun=data['Jun'], jul=data['Jul'], aug=data['Aug'], sep=data['Sep'], oct=data['Oct'], nov=data['Nov'], dec=data['Dec'],   
        aapr=ai_pred['Apr'], amay=ai_pred['May'], ajun=ai_pred['Jun'], ajul=ai_pred['Jul'], aaug=ai_pred['Aug'], asep=ai_pred['Sep'], aoct=ai_pred['Oct'], anov=ai_pred['Nov'], adec=ai_pred['Dec'], ai_sug=ai_sug,
                                segment="dashboard")
    elif g.investor:
        return render_template("investor/dashboard.html", segment="dashboard")
    return redirect('/login')

@app.route('/dashboard/startups', methods=['GET', 'POST'])
def startups():
    if g.investor:
        data = db.collection('innovators').get()
        names = [i.to_dict()['name'] for i in data]
        one_liners = [i.to_dict()['portfolio']['one_liner'] for i in data]
        return render_template('investor/startups.html', mentee_names=names, mentee_reg_nos=one_liners,ldata=list(range(len(data))), segment="startups")
    return redirect('/login')
@app.route('/dashboard/investors', methods=['GET', 'POST'])
def investors():
    if g.innovator:
        return render_template('innovator/investors.html')
    return redirect('/login')
@app.route('/dashboard/ai_chat', methods=['GET', 'POST'])
def ai_chat():
    if g.investor:
        return render_template('innovator/ai_chat.html')
    return redirect('/login')

@app.route('/dashboard/profile', methods=['GET', 'POST'])
def profile():
    if g.innovator:
        data = db.collection('innovators').get()
        portfolio = data[0].to_dict()['portfolio'] 
        print(portfolio)
        return render_template('innovator/profile.html', name=portfolio['name'], segment="profile")
    return redirect('/login')

@app.route('/dashboard/portfolio', methods=['GET', 'POST'])
def portfolio():
    if g.innovator:
        if request.method == 'POST':
                print(request.form.to_dict())
                db.collection('innovators').document(g.innovator).update({'portfolio':request.form.to_dict()})
                print("portfolio added")
        else:
            return render_template('innovator/portfolio.html', segment="portfolio")
    return redirect('/login')
@app.route('/dashboard/growth', methods=['GET', 'POST'])
def growth():
    if g.innovator:
        if request.method == 'POST':
                print(request.form.to_dict())
                db.collection('innovators').document(g.innovator).update({'growth':request.form.to_dict()})
                print("Growth added")
        else:
            return render_template('innovator/growth.html', segment="growth")
    return redirect('/login')

@app.route("/logout")
def logout():
    session.pop('investor', None)
    session.pop('innovator', None)
    session.pop('mentor', None)
    print("Logged out")
    return redirect('/login')


def get_growth(innovator):
    data = db.collection('innovators').document(innovator).get().to_dict()
    return data['growth']

def get_portfolio(innovator):
    data = db.collection('innovators').document(innovator).get().to_dict()
    return data['portfolio']

@app.route('/')
def index():
    return render_template('index.html')

@app.before_request
def before_request():
    g.investor, g.innovator, g.mentor = None, None, None
    if 'investor' in session:
        g.investor = session['investor']
    elif 'innovator' in session:
        g.innovator = session['innovator']
    elif 'mentor' in session:
        g.mentor = session['mentor']


if __name__ == '__main__':
    app.run()
