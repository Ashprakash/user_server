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


def add_post():
    Posts = mongo.db.Posts
    posttitle = request.json['post_title']
    posttags = request.json['post_tags']
    content = request.json['post_content']
    upvotes = request.json['up-votes']
    downvotes = request.json['down-votes']
    new_post = Posts.insert(request.json)
    # return Response(dumps({'status': 'Successfully inserted new post', 'post': new_post}), status=200)
    return Posts