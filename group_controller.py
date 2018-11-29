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

def adduser_group(request, user):
    Group = mongo.db.Group
    group_existing = Group.find_one({'code': request.json['code']})
    if(group_existing == None):
        return Response(dumps({'status': 'No Group availale. You can create one'}), status=403)
    if(group_existing['users'].__contains__(user['user_name'])):
        return Response(dumps({'status': 'User already exists'}), status=403)
    group_existing['users'].append(user['user_name'])
    Group.update_one({'code': request.json['code']}, {"$set": group_existing}, upsert=False)
    return Response(dumps(group_existing), status=200)


def get_group(request):
    Group = mongo.db.Group
    query = request.query_string.split("=")
    groups = Group.find({"title" : {"$regex" : ".*"+query[1]+".*"}})
    return Response(dumps(groups), status=200)


def get_user_group(request, user):
    Group = mongo.db.Group
    groups = Group.find({"users": user['user_name']})
    return Response(dumps(groups), status=200)


def create_group_obj(request, user):
    obj= {}
    obj['users'] = []
    obj['group_creator'] = user['user_name']
    obj['title'] = request.json['title']
    obj['code'] = request.json['code']
    obj['created_time'] = datetime.datetime.now()
    obj['users'].append(obj['group_creator'])
    return obj


