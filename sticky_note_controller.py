from flask import Flask, request
from flask import Response
from bson.objectid import ObjectId
from flask import jsonify
from flask_pymongo import PyMongo
from bson.json_util import dumps
import study_global
from bson import json_util, ObjectId
import json
import datetime
import bcrypt
from bson.objectid import ObjectId


app = Flask(__name__)
app.config["MONGO_URI"] = study_global.URI
mongo = PyMongo(app)


def create_sticky_note(request, user):
    StickyNote = mongo.db.StickyNote
    obj = {}
    obj['content'] = request.json['content']
    obj['user_name'] = user['user_name']
    obj['valid'] = True
    obj['created_time'] = datetime.datetime.now()
    obj = StickyNote.insert(obj)
    return Response(dumps({'status': True, 'data': obj}), status=200)


def get_sticky_note(user):
    stickyNote = mongo.db.StickyNote.find({'user_name' : user['user_name'], 'valid': True})
    return Response(dumps(stickyNote), status=200)


def invalidate_sticky_note(request, user):
    stickyNote = mongo.db.StickyNote.find_one({'_id': ObjectId(request.json['id']), "valid": True})
    if not stickyNote:
        return Response(dumps({'status': 'Note is already removed'}), status=200)
    else:
        stickyNote['valid'] = False
        stickyNote['invalidated_time'] = datetime.datetime.now()
        mongo.db.StickyNote.update_one({'_id': stickyNote['_id']}, {"$set": stickyNote}, upsert=False)
    return Response(dumps(stickyNote), status=200)

