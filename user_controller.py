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


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/studygenie"
mongo = PyMongo(app)


def create_group():
    Groups = mongo.db.Groups
    Users = mongo.db.Users
    return Response(dumps({'status': True}), status=200)