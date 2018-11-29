from flask import Flask, request
from flask import Response
from flask import jsonify
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson import json_util, ObjectId
import json
import datetime
import bcrypt
import course_controller
import post_controller
import graph_controller
import group_controller
import study_global
import sticky_note_controller
from bson.objectid import ObjectId


def newEncoder(o):
    if type(o) == ObjectId:
        return str(o)
    return o.__str__

app = Flask(__name__)


app.config["MONGO_URI"] = study_global.URI
mongo = PyMongo(app)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/circlegraph', methods=['GET'])
def get_circlegraph():
    return graph_controller.get_circlegraph()

@app.route('/tagcloud', methods=['GET'])
def get_tagcloud():
    return graph_controller.get_tagcloud()

@app.route('/user', methods=['GET'])
def get_users():
    user_cursor = mongo.db.User.find()
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


@app.route('/register', methods= ['POST'])
def save_users():
    Users = mongo.db.User
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
    userLogs = mongo.db.UserLog
    if request.form['type'] == 'interactions':
        userLogs.insert(create_event(request.form))
    else:
        userLogs.insert(create_emotion(request.form))
    return Response(dumps({'status': 'Successfully saved'}), status=200)


@app.route('/login', methods= ['POST'])
def login():
    Users = mongo.db.User
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
                Login.insert(login_user)
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
    if not logged_in:
        return Response(dumps({'status': '"User is not logged in"'}), status=403)
    else:
        logged_in['online'] = False
        logged_in['logged_out_time'] = datetime.datetime.now()
        Login.update_one({'_id': logged_in['_id']}, {"$set": logged_in}, upsert=False)
    return Response(dumps({'status': 'Successfully logged out'}), status=200)


@app.route('/create/subtopics', methods= ['POST'])
def create_sub_topics():
    return course_controller.create_sub_topics()


@app.route('/upvote', methods=['POST'])
def upvote_post():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    posts = post_controller.upvote_post(request, user_obj)
    return "Successfully updated"


@app.route('/downvote', methods=['POST'])
def downvote_post():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    posts = post_controller.downvote_post(request, user_obj)
    return "Successfully updated"

@app.route('/pin-post', methods=['POST'])
def pin_post():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    posts = post_controller.pin_post(request, user_obj)
    return "Successfully updated"

@app.route('/unpin-post', methods=['POST'])
def unpin_post():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    posts = post_controller.unpin_post(request, user_obj)
    return "Successfully updated"

@app.route('/get-posts', methods=['GET'])
def get_posts_group():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    posts = post_controller.get_posts(request, user_obj)
    return Response(json.dumps(posts,default = myconverter), status=200)


@app.route('/create/sticky/note', methods= ['POST'])
def create_sticky_note():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    return sticky_note_controller.create_sticky_note(request, user_obj)


@app.route('/invalidate/sticky/note', methods= ['POST'])
def invalidate_sticky_note():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    return sticky_note_controller.invalidate_sticky_note(request, user_obj)


@app.route('/courses', methods= ['GET'])
def get_courses():
    return course_controller.get_course()


@app.route('/sticky/notes', methods= ['GET'])
def get_sticky_notes():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    return sticky_note_controller.get_sticky_note(user_obj)


@app.route('/create/post', methods= ['POST'])
def create_new_post():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    posts = post_controller.add_post(request, user_obj)
    return posts

@app.route('/create/group/post', methods= ['POST'])
def create_new_post_group():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    posts = post_controller.add_post(request, user_obj)
    return posts

@app.route('/create/comments/post', methods= ['POST'])
def create_new_comment():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    posts = post_controller.create_comment(request, user_obj)
    return "Successfully added the comment"


@app.route('/get/groups', methods= ['GET'])
def get_groups():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    return group_controller.get_group(request)


@app.route('/get/groups/user', methods= ['GET'])
def get_user_groups():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    return group_controller.get_user_group(request, user_obj)


@app.route('/sub/topics', methods= ['GET'])
def get_sub_topics():
    return course_controller.get_sub_topic(request)


@app.route('/create/group', methods= ['POST'])
def create_new_group():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    group = group_controller.create_group(request , user_obj)
    return group

@app.route('/add-user/group', methods= ['POST'])
def add_user_to_group():
    user_obj = find_user(request.headers)
    if user_obj == 403:
        return Response(dumps({'status': 'Error unauthorized access'}), status=403)
    group = group_controller.adduser_group(request , user_obj)
    return group

@app.route('/analytics/user-events', methods= ['GET'])
def getUserEvents():
    userLogs = mongo.db.UserLog
    userLog_data = userLogs.find({'type': 'interactions'})
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


@app.route('/analytics/user-emotions', methods= ['GET'])
def getEmotions():
    userLogs = mongo.db.UserLog
    userLog_data = userLogs.find({'type': 'emotions'})
    response = {}
    for user in userLog_data:
        if user['user_name'] not in response.keys():
            response[user['user_name']] = {}
            response[user['user_name']]['user_name'] = user['user_name']
            response[user['user_name']]['actions'] = ['smile', 'cheekRaise', 'browRaise', 'smirk', 'attention', 'eyeClosure', 'chinRaise', 'eyeWiden'];
            response[user['user_name']]['count'] = [ 0, 0, 0, 0, 0, 0, 0, 0]

        if float(user['smile']) > 90:
            response[user['user_name']]['count'][0] =  response[user['user_name']]['count'][0] + 1
        if float(user['cheekRaise']) > 90:
            response[user['user_name']]['count'][1] = response[user['user_name']]['count'][1] + 1
        if float(user['browRaise']) > 90:
            response[user['user_name']]['count'][2] = response[user['user_name']]['count'][2] + 1
        if float(user['smirk']) > 90:
            response[user['user_name']]['count'][3] = response[user['user_name']]['count'][3] + 1
        if float(user['attention']) > 90:
            response[user['user_name']]['count'][4] = response[user['user_name']]['count'][4] + 1
        if float(user['eyeClosure']) > 50:
            response[user['user_name']]['count'][5] = response[user['user_name']]['count'][5] + 1
        if float(user['chinRaise']) > 0.5:
            response[user['user_name']]['count'][6] = response[user['user_name']]['count'][6] + 1
        if float(user['eyeWiden']) > 90:
            response[user['user_name']]['count'][7] = response[user['user_name']]['count'][7] + 1
    return Response(json.dumps(response.values()), status=200)


@app.route('/analytics/user-targets', methods=['GET'])
def getUserTargets():
    userLogs = mongo.db.UserLog
    userLog_data = userLogs.find({'type': 'interactions'})
    response = {}
    for user in userLog_data:
        if user['user_name'] not in response.keys():
            response[user['user_name']] = {}
            response[user['user_name']]['user_name'] = user['user_name']
            response[user['user_name']]['arr'] = []
            response[user['user_name']]['target'] = []

        idx = -1
        try:
            idx = response[user['user_name']]['arr'].index(user['target'])
        except ValueError:
            ""
        if idx >= 0:
            response[user['user_name']]['target'][idx]['value'] = response[user['user_name']]['target'][idx]['value'] + 1
        else:
            data = {"name" : user['target'], 'value': 1}
            response[user['user_name']]['target'].append(data)
            response[user['user_name']]['arr'].append(user['target'])

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


def find_user(header):
    Login = mongo.db.Login
    token =  header['Authorization']
    loggedInUser = Login.find_one({"online": True, "token": token})
    if loggedInUser is None:
        return 403
    return loggedInUser


def create_user_dto(each, loggedin):
    user= {}
    user['user_name'] = each['user_name']
    user['first_name'] = each['first_name']
    user['last_name'] = each['last_name']
    user['email'] = each['email']
    if loggedin:
        user['logged_in_time'] = str(loggedin['logged_in_time'])
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


def create_emotion(form):
    emotion= {}
    emotion['smile'] = form['smile']
    emotion['innerBrowRaise'] = form['innerBrowRaise']
    emotion['browRaise'] = form['browRaise']
    emotion['upperLipRaise'] = form['upperLipRaise']
    emotion['chinRaise'] = form['chinRaise']
    emotion['mouthOpen'] = form['mouthOpen']
    emotion['smirk'] = form['smirk']
    emotion['eyeClosure'] = form['eyeClosure']
    emotion['attention'] = form['attention']
    emotion['eyeWiden'] = form['eyeWiden']
    emotion['cheekRaise'] = form['cheekRaise']
    emotion['user_name'] = form['user_name']
    emotion['type'] = form['type']
    return emotion
def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

if __name__ == '__main__':
    app.run()
