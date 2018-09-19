from flask import Flask, request
from flask import Response
from flask import jsonify
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson import json_util, ObjectId
import json
import datetime
import bcrypt
from bson.objectid import ObjectId


def newEncoder(o):
    if type(o) == ObjectId:
        return str(o)
    return o.__str__

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/adaptive"
mongo = PyMongo(app)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/user', methods=['GET'])
def get_users():
    user_cursor = mongo.db.Users.find()
    user_name = set()
    users = []
    for each in user_cursor:
        if each['user_name'] not in user_name:
            users.append(each)
        user_name.add(each['user_name'])

    query = {}
    sort = [(u"logged_in_time", -1)]
    logged_in = mongo.db.Login.find(query, sort=sort)
    logs = []
    for log in logged_in:
        if log['user_name'] in user_name:
            logs.append(log)
        if len(user_name) == len(logs):
            break

    response = []
    user_name = []
    for each in users:
        found = False
        for log in logs:
            if each['user_name'] == log['user_name']:
                user_name.append(each['user_name'])
                response.append(create_user_dto(each, log))
                found = True
                break
        if not found:
            response.append(create_user_dto(each, log))
    return Response(dumps(response), status=200)

@app.route('/user', methods= ['POST'])
def save_users():
    Users = mongo.db.Users
    username = request.json['user_name']
    password = request.json['password']
    hashed = encrypt(password)
    print(hashed)
    request.json['password'] = hashed
    exist_user = Users.find_one({'user_name': username})

    if exist_user == None:
        saved_user = Users.insert(request.json)
        return Response(dumps({'status': 'Successfully saved', 'user': saved_user}), status=200)
    else:
        return Response(dumps({'status': 'Username already exist'}), status=404)


@app.route('/log', methods= ['POST'])
def save_logs():
    userLogs = mongo.db.UserLogs
    userLogs.insert(create_event(request.form))
    return Response(dumps({'status': 'Successfully saved'}), status=200)


@app.route('/login', methods= ['POST'])
def login():
    Users = mongo.db.Users
    Login = mongo.db.Login
    username = request.json['user_name']
    password = request.json['password']
    exist_user = Users.find_one({'user_name': username})
    logged_in = Login.find_one({'user_name': username, "online": True})
    if logged_in:
        return Response(dumps("User is already loggedin"), status=403)
    else:
        if exist_user:
            hashed = exist_user['password']
            if check_password(password, hashed):
                login_user = create_log_in(exist_user)
                login_user['token'] = username + "-token"
                # login_user = Login.insert(login_user)
                return Response(dumps({'status': True, 'data': login_user}), status=200)
            else:
                return Response(dumps({'status': False}), status=401)
        else:
            return Response(dumps("No Users exist"), status=404)


@app.route('/logout', methods= ['POST'])
def logout():
    Login = mongo.db.Login
    username = request.json['user_name']
    logged_in = Login.find_one({'user_name': username, "online": True})
    if logged_in == None:
        return dumps("User is not logged in")
    else:
        logged_in['online'] = False
        logged_in['logged_out_time'] = datetime.datetime.now()
        Login.update_one({'_id': logged_in['_id']}, {"$set": logged_in}, upsert=False)
    return Response(dumps({'status': 'Successfully logged out'}), status=200)


@app.route('/analytics/user-events', methods= ['GET'])
def getUserEvents():
    userLogs = mongo.db.UserLogs
    userLog_data = userLogs.find()
    event = ['click', 'focus', 'blur', 'keyup', 'keydown', 'keypressed', 'mousemove', 'resize', 'scroll']
    response = {}
    for user in userLog_data:
        if user['user_name'] not in response.keys():
            response[user['user_name']] = {}
            response[user['user_name']]['user_name'] = user['user_name']
            response[user['user_name']]['event'] = event
            response[user['user_name']]['count'] = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        idx = -1
        try:
            idx = response[user['user_name']]['event'].index(user['event'])
        except ValueError:
            ""
        if idx >= 0:
            response[user['user_name']]['count'][idx] = response[user['user_name']]['count'][idx] + 1

    return Response(json.dumps(response.values()), status=200)


@app.route('/analytics/user-targets', methods= ['GET'])
def getUserTargets():
    userLogs = mongo.db.UserLogs
    userLog_data = userLogs.find()
    response = {}
    for user in userLog_data:
        if user['user_name'] not in response.keys():
            response[user['user_name']] = {}
            response[user['user_name']]['user_name'] = user['user_name']
            response[user['user_name']]['target'] = []
            response[user['user_name']]['count'] = []
        idx = -1
        try:
            idx = response[user['user_name']]['target'].index(user['target'])
        except ValueError:
            ""
        if idx >= 0:
            response[user['user_name']]['count'][idx] = response[user['user_name']]['count'][idx] + 1
        else:
            response[user['user_name']]['target'].append(user['target'])
            response[user['user_name']]['count'].append(1)

    return Response(json.dumps(response.values()), status=200)


def create_log_in(user):
    login = {}
    login['user_name'] = user['user_name']
    login['logged_in_time'] = datetime.datetime.now()
    login['online'] = True
    return login


def encrypt(password):
    hashed = bcrypt.hashpw(b''+password.encode('utf-8'), bcrypt.gensalt())
    print(hashed)
    return hashed


def check_password(password, hashed):
    if bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')):
        return True
    else:
        return False

def create_user_dto(each, loggedin):
    user= {}
    user['user_name'] = each['user_name']
    user['first_name'] = each['first_name']
    user['last_name'] = each['last_name']
    user['email'] = each['email']
    if loggedin:
        user['logged_in_time'] = loggedin['logged_in_time']
        user['online'] = loggedin['online']
    else:
        user['logged_in_time'] = ''
        user['online'] = False
    return user

def create_event(form):
    event = {}
    event['event'] = form['Event']
    event['target'] = form['Target']
    event['x'] = form['x']
    event['y'] = form['y']
    event['scrollTop'] = form['scrollTop']
    event['xtra'] = form['xtra']
    event['value'] = form['value']
    event['user_name'] = form['user_name']
    event['date'] = form['date']
    return event

if __name__ == '__main__':
    app.run()
