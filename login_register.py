from db import User, Asset, Location, Transaction, start_database, get_session
import bcrypt
from datetime import datetime, timezone
import time

start_database()
session = get_session()
user = None

def get_asset_by_symbol(symbol):
    return session.query(Asset).filter(Asset.symbol == symbol).first()


def get_location_by_name(name):
    return session.query(Location).filter(Location.name == name).first()


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def get_user_by_email(email):
    return session.query(User).filter(User.email == email).first()


def login():
    email = input("Email --> ")
    global user
    user = get_user_by_email(email)
    if user is None:
        print("\nAn account with this email does not exist; would you like to register?\n\n1) Yes\n2) No, try again")
        while True:
            user_choice = input("--> ")
            if user_choice is '1':
                return '2'
            elif user_choice is '2':
                return '1'
    else:
        password = input("Password --> ")
        valid = bcrypt.checkpw(password.encode('utf-8'), user.password_hash)
        del password
        if valid:
            print("\nLogin success!\n")
            return '0'
        else:
            print("\nWrong password!\n")
            return '1'


def register():
    name = input("Name --> ")
    email = input("Email --> ")
    global user
    user = get_user_by_email(email)
    if user is not None:
        print("\nAn account with this email is already registered; would you like to login?\n\n1) Yes\n2) No, try again")
        while True:
            user_choice = input("--> ")
            if user_choice is '1':
                return '1'
            elif user_choice is '2':
                return '2'
    password = input("Password --> ")
    new_user = User(name=name, email=email, password_hash=hash_password(password))
    del password
    print()
    session.add(new_user)
    session.commit()
    return '0'


def login_register():
    print("\n----- Digital Asset Portfolio Manager v0.1 -----\n")

    print("1) Login")
    print("2) Register")

    login_choice = '0'
    while login_choice is not '1' and login_choice is not '2':
        login_choice = input("--> ")

    while login_choice is '1' or login_choice is '2':
        print()
        if login_choice is '1':
            login_choice = login()
        elif login_choice is '2':
            login_choice = register()


def get_user():
    return user

