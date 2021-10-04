
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

    # 모의고사 점수내기
    member_test_score = score.Member_Test()

    answer_list = ['제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.']

    # Storage에서 mp3 파일 다운받기
    storage_audio_path = 'User/32f306540a19e3e9/No5_32f306540a19e3e9_20211004_030835_test.mp3'

    local_audio_path = './Audio/' + storage_audio_path[-45:]
    storage.child(storage_audio_path).download(local_audio_path)

    part_score = member_test_score.evaluate(local_audio_path, answer_list[0])

    return part_score
    # return render_template("main.html")

@app.route('/post',methods=["POST"])
def hello_post():
    android_id = request.form['android_id']
    test_type = request.form['test_or_verify']
    start_date = request.form['date_time']


    # 모의고사 점수내기
    member_test_score = score.Member_Test()
    answer_list = ['제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.']


    # 날짜, 시간 데이터 준비하기
    test_id = "test_" + start_date[1:]
    android_db_id = "android_" + android_id

    storage_audio_paths = ""

    # 파이어베이스 Storage에서 데이터 가져오기 
    for i in range(2):

        # Storage에서 mp3 파일 다운받기
        part_url_name = 'part' + str(i + 1) + '_url'
        storage_audio_path = request.form[part_url_name]

        local_audio_path = './Audio/' + storage_audio_path[-45:]
        storage.child(storage_audio_path).download(local_audio_path)

        # 채점하기
        part_score = member_test_score.evaluate(local_audio_path, answer_list[i])

        # 파트 id
        # part_id = "part_" + str(i)

        # # 안드스튜디오에서 다른 파트도 추가하면됨, 확인테스트도 봐야함
        # db.child("member").child(android_db_id).child(test_type).update({
        #     test_id : {
        #         part_id : {
        #             "similarity": part_score['유사도'],
        #             "pronunciation": part_score['발음평가'],
        #             "fluency": part_score['유창성'],
        #             "expression": part_score['표현력'],
        #             "relevance": part_score['주제의 연관성'],
        #             "url": storage_audio_path
        #         }
        #     }
        # })

        storage_audio_paths += storage_audio_path


    # score.py 완성되기 전까지 서버 통신 코드
    # db.child("member").child(android_db_id).child(test_type).update({
    #     test_id : {
    #         part_id : {
    #             "similarity": 100,
    #             "pronunciation": 100,
    #             "fluency": 100,
    #             "expression": 100,
    #             "relevance": 100,
    #             "url": url
    #         }
    #     }
    # })

    return storage_audio_paths
    # return ('서버 통신 완료')



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
