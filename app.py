from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///airport.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  
app.config['MAIL_PASSWORD'] = 'your_password'  


db = SQLAlchemy(app)
socketio = SocketIO(app)
mail = Mail(app)


class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), unique=True, nullable=False)
    departure_city = db.Column(db.String(100), nullable=False)
    arrival_city = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='On Time')


class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=False)
    flight = db.relationship('Flight', backref=db.backref('passengers', lazy=True))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    flights = Flight.query.all()
    return render_template('index.html', flights=flights)

@app.route('/checkin', methods=['POST'])
def checkin():
    passenger_name = request.form.get('name')
    flight_id = request.form.get('flight_id')
    flight = Flight.query.get(flight_id)
    if flight:
        passenger = Passenger(name=passenger_name, flight_id=flight_id)
        db.session.add(passenger)
        db.session.commit()
        return redirect(url_for('index'))
    return 'Flight not found'

@app.route('/send_boarding_pass/<int:passenger_id>')
def send_boarding_pass(passenger_id):
    passenger = Passenger.query.get(passenger_id)
    if passenger:
        msg = Message('Your Boarding Pass', sender='your_email@gmail.com', recipients=[passenger.name])
        msg.body = f"Here is your boarding pass for flight {passenger.flight.flight_number}"
        mail.send(msg)
        return 'Boarding pass sent!'
    return 'Passenger not found'

@socketio.on('track_flight')
def track_flight(flight_number):
    flight = Flight.query.filter_by(flight_number=flight_number).first()
    if flight:
        emit('flight_status', {'status': flight.status})

if __name__ == '__main__':
    socketio.run(app, debug=True)
