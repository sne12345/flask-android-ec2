
from flask import Flask
from flask import request
from flask import jsonify
from flask import redirect, url_for, send_from_directory, render_template
import json
import pyrebase

app = Flask(__name__)

# login으로 변경해야함
config = {
   "apiKey": "AIzaSyASyU5Qxe0zJZDVT1-oTYEVIcDYJzZNdA8",
   "authDomain": "aitutor-894f0.firebaseapp.com",
   "databaseURL": "https://aitutor-894f0-default-rtdb.firebaseio.com",
   "projectId": "aitutor-894f0",
   "storageBucket": "aitutor-894f0.appspot.com",
   "messagingSenderId": "145018138005",
   "appId": "1:145018138005:web:ea124ef3292ae2d0cb5a9c",
   "measurementId": "G-0YF0B8C5EC"
}

# # db settings
firebase = pyrebase.initialize_app(config)
db = firebase.database()

db.child("member").child("asdf").child("test").child("part_sdfdf").push({
    "similarity": 94, "pronunciation": 41,
    "fluency": 53,
    "expression": 64,
    "relevance": 72,
    "url": "sdfsdfdsfs"})




@app.route('/')
def hello_world():
    return render_template("main.html")
    # return "Hello World"

@app.route('/post',methods=["POST"])
def hello_post():
    android_id = request.form['android_id']
    print(android_id)

    test_or_verify = request.form['test_or_verify']
    print(test_or_verify)

    part = request.form['part']
    print(part)

    url = request.form['url']
    print(url)

    # # db settings
    firebase = pyrebase.initialize_app(config)
    db = firebase.database()

    # db.child("member").child(android_id).child(test_or_verify).child(part).push({
    #     "similarity": 94, "pronunciation": 41,
    #     "fluency": 53,
    #     "expression": 64,
    #     "relevance": 72,
    #     "url": url[1:]})

    db.child("member").child(android_id).child(test_or_verify).push({
        part: {
        "similarity": 94, "pronunciation": 41,
        "fluency": 53,
        "expression": 64,
        "relevance": 72,
        "url": url[1:]}})

    return ('서버 통신 : ' + android_id+','+test_or_verify+','+part+','+url)

@app.route('/one')
def hello_one():
    return "Hello one"


@app.route('/two')
def hello_two():
    return "Hello two"



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
