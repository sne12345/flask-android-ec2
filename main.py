from flask import Flask
from flask import request
from flask import jsonify
from flask import redirect, url_for, send_from_directory, render_template
import json
import pyrebase
import pickle
from konlpy.tag import Komoran
import score

app = Flask(__name__)
model = pickle.load(open('model/ko.pkl', 'rb'))
komoran = Komoran()

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


@app.route('/word2vec', methods=['GET'])
def sim_score():
    data = request.get_json(force=True)

    sim_list = []
    for a in data['answer']:
        for u in data['user']:
            try:
                sim_list.append(model.wv.similarity(a, u))
            except:
                pass
    if sim_list:
        output = int(sum(sim_list) / len(sim_list) * 100)
        return jsonify(output)
    else:
        return None


@app.route('/post', methods=["POST"])
def hello_post():
    android_id = request.form['android_id']
    test_type = request.form['test_or_verify']
    start_date = request.form['date_time']

    # 모의고사 점수내기
    member_test_score = score.Member_Test()
    answer_list = ['제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.',
                   '직진 후 좌회전하고 도서관이 보이면 우회전을 해주세요. 왼쪽에 기숙사가 보일거에요. 그곳에 내려주시면 됩니다.',
                   '민수씨는 대회 전날에 춤 연습을 하였습니다. 대회 당일에는 다른 팀이 공연하는 것을 관람하였습니다. 민수씨네 팀도 공연을 하였으며 우승을 차지하였습니다.',
                   '안내문을 보지 못 하는 경우도 있을 수 있어요. 놀이터를 관리하는 관리인을 두고 어린이들이 사용하지 못하도록 관리하는 건 어떨까요?',
                   '인터넷 금융 거래 이용률이 2010년 25퍼센트에서 2020년 60퍼센트로 크게 증가하면서 은행 지점을 이용하는 사람은 10년 동안 천 개 이상  줄었습니다.',
                   '리더는 구성원들이 자발적, 의욕적으로 역량을 발휘할 수 있도록 환경을 조성해주는 것입니다.']

    # 날짜, 시간 데이터 준비하기
    test_id = "test_" + start_date[1:]
    android_db_id = "android_" + android_id

    storage_audio_paths = ""

    total_score = {'similarity': 0, 'pronunciation': 0, 'fluency': 0, 'expression': 0, 'relevance': 0}

    # 파이어베이스 Storage에서 데이터 가져오기
    for i in range(6):
        # Storage에서 mp3 파일 다운받기
        part_url_name = 'part' + str(i + 1) + '_url'
        storage_audio_path = request.form[part_url_name]

        local_audio_path = '/home/ubuntu/flask-android-ec2/Audio/' + storage_audio_path[-45:]
        storage.child(storage_audio_path).download(local_audio_path)

        # 채점하기
        part_score = member_test_score.evaluate(local_audio_path, answer_list[i], komoran)
        print(part_score)

        # 파트 id
        part_id = "part_" + str(i)

        # # 안드스튜디오에서 다른 파트도 추가하면됨, 확인테스트도 봐야함
        db.child("member").child(android_db_id).child(test_type).update({
            test_id: {
                part_id: {
                    "similarity": part_score['similarity'],
                    "pronunciation": part_score['pronunciation'],
                    "fluency": part_score['fluency'],
                    "expression": part_score['expression'],
                    "relevance": part_score['correlation'],
                    "url": storage_audio_path
                }
            }
        })
        total_score['similarity'] += part_score['similarity']
        total_score['pronunciation'] += part_score['pronunciation']
        total_score['fluency'] += part_score['fluency']
        total_score['expression'] += part_score['expression']
        total_score['relevance'] += part_score['correlation']

    result_score = str(total_score['similarity'] / 6) + ' ' + str(total_score['pronunciation'] / 6) + ' ' + str(
        total_score['fluency'] / 6) + ' ' + str(total_score['expression'] / 6) + ' ' + str(total_score['relevance'] / 6)

    return result_score

@app.route('/score', methods=['GET'])
def test_score():
    data = request.get_json(force=True)
    fname = '/home/ubuntu/flask-android-ec2/Audio/KOR_F_RM0769FLJH0325.mp3'
    member_test_score = score.Member_Test()
    output = member_test_score.evaluate(fname,data['answer'],komoran)
    #output = "안녕 ?"
    if output:
        return jsonify(output)
    else:
        print('채점 실패')
        return {'correlation': 0, 'expression': 0, 'fluency': 0, 'pronunciation': 0, 'similarity': 0}



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
