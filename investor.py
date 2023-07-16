from flask import Blueprint, render_template, redirect, g

investor = Blueprint('investor', __name__, static_folder='static', template_folder='templates')

@investor.route("/login")
def investor_login():
    return render_template("investor/sign-in.html")

@investor.route('/dashboard')
def investor_dashboard():
    if g.investor:
        return render_template("investor/dashboard.html")
    return redirect("/investor/login")

@investor.route('/dashboard/add_mentor')
def add_mentor():
    if g.investor:
        return render_template("investor/add_mentor.html")
    return render_template("/investor/sign-in.html")