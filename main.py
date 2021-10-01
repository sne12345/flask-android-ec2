
from flask import Flask
from flask import request
from flask import jsonify
from flask import redirect, url_for, send_from_directory, render_template
import json
import pyrebase
import score

app = Flask(__name__)


# # 파이어베이스 계정 : Login
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
storage = firebase.storage()



@app.route('/')
def hello_world():
    return render_template("main.html")
    # return "Hello World"

@app.route('/post',methods=["POST"])
def hello_post():
    android_id = request.form['android_id']
    test_type = request.form['test_or_verify']
    part_id = request.form['part']
    url = request.form['url']
    date_time = request.form['date_time']


    # 파이어베이스 Storage에서 데이터 가져오기 => 파일 올라오는데는 시간 좀 걸림, 그래도 점수내기는 가능
    # 평가 후에 로컬에서 삭제하는 것도 구현할 것
    # path_on_storage_and_local = 'User' + android_id + '/' + url
    # storage.child(path_on_storage_and_local).download(path_on_storage_and_local)

    # 모의고사 점수내기
    # member_test_score = score.Member_Test()
    # total_score = member_test_score.evaluate(path_on_storage_and_local)
    # print(total_score)


    # 날짜, 시간 데이터 받아오기
    test_id = "test_" + date_time[1:]
    android_db_id = "android_" + android_id

    # 안드스튜디오에서 다른 파트도 추가하면됨, 확인테스트도 봐야함
    # db.child("member").child(android_db_id).child(test_type).update({
    #     test_id : {
    #         part_id : {
    #             "similarity": total_score['유사도'],
    #             "pronunciation": total_score['발음평가'],
    #             "fluency": total_score['유창성'],
    #             "expression": total_score['표현력'],
    #             "relevance": total_score['주제의 연관성'],
    #             "url": url[1:]
    #         }
    #     }
    # })

    # score.py 완성되기 전까지 서버 통신 코드
    db.child("member").child(android_db_id).child(test_type).update({
        test_id : {
            part_id : {
                "similarity": 100,
                "pronunciation": 100,
                "fluency": 100,
                "expression": 100,
                "relevance": 100,
                "url": url[1:]
            }
        }
    })

    return ('서버 통신 완료')



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
