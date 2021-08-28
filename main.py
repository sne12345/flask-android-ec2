
from flask import Flask
from flask import request
from flask import jsonify
from flask import redirect, url_for, send_from_directory, render_template
import json
import pyrebase

app = Flask(__name__)

# 파이어베이스 계정세팅
config = {
  "apiKey": "AIzaSyDH9vnpXL_qMtFLjm7YbA_2p9S5vUYmd_8",
  "authDomain": "login-34159.firebaseapp.com",
  "databaseURL": "https://login-34159-default-rtdb.firebaseio.com",
  "projectId": "login-34159",
  "storageBucket": "login-34159.appspot.com",
  "messagingSenderId": "930147078212",
  "appId": "1:930147078212:web:d4904676bf467f12036c11",
  "measurementId": "G-EP22J4P7YQ"
}

# # db settings
firebase = pyrebase.initialize_app(config)
db = firebase.database()


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


    # android id를 value값으로 명확하게 알 수 있게 변경하기 + 안드스튜디오에서 다른 파트도 추가하면됨, 확인테스트도 봐야함
    db.child("member").push({
        "android_id": android_id,
        "test_or_verify" : test_or_verify,
        "score" : {
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
