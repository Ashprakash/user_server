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
import study_global



app = Flask(__name__)
app.config["MONGO_URI"] = study_global.URI
mongo = PyMongo(app)

def create_group(request, user):
    Group = mongo.db.Group
    group_existing = Group.find_one({'code': request.json['code']})
    if(group_existing != None):
        return Response(dumps({'status': 'A group for this course already exits'}), status=403)

    group_object = create_group_obj(request, user)
    new_group = Group.insert(group_object)
    return Response(dumps(new_group), status=200)


def create_group_obj(request, user):
    obj= {}
    obj['group_creator'] = user['user_name']
    obj['title'] = request.json['title']
    obj['code'] = request.json['code']
    obj['created_time'] = datetime.datetime.now()
    return obj

