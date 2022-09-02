from socketserver import ThreadingUDPServer
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import os

app = Flask(__name__)

# capture the current folder path for creating the databae file
basedir = os.path.abspath(os.path.dirname(__file__))

# configure the database using flask inbuilt variables
# configure sqlite database
# create database file in the application folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'  # change this IRL(In real life)
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '01ba067a86f2d3'
app.config['MAIL_PASSWORD'] = '3682836cd80cb1'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


# Instantiate the database to the app
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)   # initialise JWT
mail = Mail(app)

# flask cli
# create, drop and seed databases


@app.cli.command('db_create')  # command to create the database
def db_create():
    db.create_all()
    print('Database created!')


@app.cli.command('db_drop')  # command to drop the database
def db_drop():
    db.drop_all()
    print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planets(planet_name='Mercury',
                      planet_type='Class D',
                      home_star='Sol',
                      mass=3.52e24,
                      radius=45.67e6,
                      distance=356.7e43)

    venus = Planets(planet_name='Venus',
                    planet_type='Class K',
                    home_star='Sol',
                    mass=4.52e24,
                    radius=90.67e2,
                    distance=675.7e4)

    earth = Planets(planet_name='Earth',
                    planet_type='Class M',
                    home_star='Sol',
                    mass=5.52e24,
                    radius=106.67e56,
                    distance=1067.9e83)

    # add this data to the table
    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    # create user
    test_user = User(first_name='Amitesh',
                     last_name='Veeragattam',
                     email='vdnamitesh@gmail.com',
                     password='@M1tesh123')

    # add user to the database
    db.session.add(test_user)
    # commit the changes, without this there wont be any saved work in the database
    db.session.commit()
    print('Database seeded!')


@app.route('/')
def hello_world():
    return 'Hello Amitesh!'


@app.route('/super_simple')
def super_simple():
    return jsonify(message='Hello World! You are on a planet')


@app.route('/params')
def params():
    name = request.args.get('label')
    age = int(request.args.get('number'))
    if age < 100:
        return jsonify(info="Sorry! " + name + ", We need more money"), 404
    else:
        return jsonify(info="Thanks for donation " + name + "!")


@app.route('/parameters/<string:name>/<int:donation>')
def parameters(name, donation):
    name = name
    donation = donation
    if donation < 100:
        return jsonify(info="Sorry! " + name + ", We need more than " + str(donation)), 404
    else:
        return jsonify(info=str(donation) + "! That will be really helpfull")


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planets.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(planets=result)


@app.route('/users', methods=['GET'])
def users():
    users_list = User.query.all()
    result = users_schema.dump(users_list)
    return jsonify(users=result)


@app.route('/all', methods=['GET'])
def all():
    planets_list = Planets.query.all()
    users_list = User.query.all()
    planets = planets_schema.dump(planets_list)
    users = users_schema.dump(users_list)
    return jsonify(planets=planets, users=users)

# user registeration route


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='Email already registered in our database!'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name,
                    email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User Registeration Successfull!"), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login Successfull', access_token=access_token)
    else:
        return jsonify(message="Incorrect email or password"), 401


@app.route('/recover_password/<string:email>', methods=['GET'])
def recover_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("your planetary API password is " + user.password,
                      sender="admin@planetary-api.com", recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent to " + email)
    else:
        return jsonify(message="Email does not exist!"), 401


@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
    planet = Planets.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(planet=result)
    else:
        return jsonify(message="Planet does not exist"), 404


@app.route('/add_planet', methods=['POST'])
@jwt_required()
def add_planet():
    planet_name = request.form['planet_name']
    test = Planets.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message="Planet is already present"), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])
        new_planet = Planets(planet_name=planet_name, planet_type=planet_type,
                             home_star=home_star, mass=mass, radius=radius, distance=distance)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="Planet added Successfully"), 201


@app.route('/update_planet', methods=['PUT'])
@jwt_required()
def update_planet():
    planet_id = int(request.form['planet_id'])
    planet = Planets.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.homestar = request.form['homestar']
        planet.mass = float(request.form['mass'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify(message="Planet updated successfully!"), 202
    else:
        return jsonify(message="Planet does not exist"), 404


@app.route('/delete_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete_planet(planet_id: int):
    planet = Planets.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message="Planet deleted successfully!"), 202
    else:
        return jsonify(message="Planet is not available"), 404


class UserSchema(ma.Schema):
    class Meta():
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta():
        fields = ('planet_id', 'planet_name', 'planet_type',
                  'home_star', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


# database section
# database class for users
class User(db.Model):  # .Model is a flask inbuild database method
    __tablename__ = 'users'  # this will give name to the table
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

# database for planets


class Planets(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
