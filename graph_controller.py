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

def get_circlegraph():
    dict_user_course = {}
    
    results = mongo.db.Post.find()

    for each_result in results:
    #print(each_result['created_user']['user_name'])
        user_name = each_result['created_user']['user_name']
        if user_name not in dict_user_course:
            dict_user_course[user_name] = {}
        course_code = each_result['code']
        if course_code not in dict_user_course[user_name]:
            dict_user_course[user_name][course_code] = 0
        dict_user_course[user_name][course_code] += 1

        list_strings = []
        for each_user in dict_user_course:
            for each_course in dict_user_course[each_user]:
                temp_dict = {}
                temp_dict['from'] = each_user
                temp_dict['to'] = each_course
                temp_dict['value'] = dict_user_course[each_user][each_course]
                #temp_string = "{\"from\":\"" + each_user + "\",\"to\":\"" + each_course + "\",\"value\":" + str(dict_user_course[each_user][each_course]) + "}"
                list_strings.append(temp_dict)

    return Response(dumps(list_strings), status=200)
