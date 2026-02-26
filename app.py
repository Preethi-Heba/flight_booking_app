from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flight_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# ---------------- MODELS ----------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20))
    departure = db.Column(db.String(100))
    arrival = db.Column(db.String(100))
    departure_time = db.Column(db.DateTime)
    price = db.Column(db.Integer)
    seats_available = db.Column(db.Integer, default=50)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'))

    flight = db.relationship('Flight')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists! Try another one.")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    flights = Flight.query.all()
    return render_template('dashboard.html', flights=flights)

@app.route('/add_flight', methods=['GET','POST'])
@login_required
def add_flight():
    if request.method == 'POST':
        flight = Flight(
            flight_number=request.form['flight_number'],
            departure=request.form['departure'],
            arrival=request.form['arrival'],
            departure_time=datetime.strptime(request.form['departure_time'], '%Y-%m-%dT%H:%M')
        )
        db.session.add(flight)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_flight.html')

@app.route('/book/<int:flight_id>', methods=['GET', 'POST'])
@login_required
def book(flight_id):
    flight = Flight.query.get_or_404(flight_id)

    if request.method == 'POST':

        # Check if already booked
        existing_booking = Booking.query.filter_by(
            user_id=current_user.id,
            flight_id=flight.id
        ).first()

        if existing_booking:
            flash("You already booked this flight!")
            return redirect(url_for('dashboard'))

        # Check seat availability
        if flight.seats_available > 0:
            flight.seats_available -= 1

            booking = Booking(
                user_id=current_user.id,
                flight_id=flight.id
            )

            db.session.add(booking)
            db.session.commit()

            flash("Flight booked successfully!")
            return redirect(url_for('dashboard'))
        else:
            flash("No seats available!")

    return render_template('book_flight.html', flight=flight)

@app.route('/my_bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if Flight.query.count() == 0:
            flight1 = Flight(
                flight_number="AI101",
                departure="Chennai",
                arrival="Delhi",
                departure_time=datetime.now(),
                price=5000,
                seats_available=50
            )

            flight2 = Flight(
                flight_number="AI202",
                departure="Mumbai",
                arrival="Bangalore",
                departure_time=datetime.now(),
                price=4000,
                seats_available=30
            )

            db.session.add(flight1)
            db.session.add(flight2)
            db.session.commit()

    app.run(debug=True, port=5002)