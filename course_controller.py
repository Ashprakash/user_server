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


def create_sub_topics():
    Courses = mongo.db.Courses
    SubTopics = mongo.db.SubTopics
    subtopics = request.json

    for topic in subtopics:
        course = Courses.find_one({'code': topic['code']})
        topic['course'] = course
        topic = SubTopics.insert(topic)
    return Response(dumps({'status': True, 'data': subtopics}), status=200)


def get_course():
    courses = mongo.db.Courses.find()
    return Response(dumps(courses), status=200)


def get_sub_topic(request):
    query = request.query_string.split("=")
    subtopics = mongo.db.SubTopics.find({ 'code': query[1]})
    return Response(dumps(subtopics), status=200)