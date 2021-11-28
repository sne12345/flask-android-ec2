
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
model = pickle.load(open('model/ko.pkl','rb'))
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

@app.route('/get',methods=["GET"])
def hello_get():

    # 모의고사 점수내기
    member_test_score = score.Member_Test()
    answer_list = ['제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','아니요, 기사님. 학교 안에 있는 기숙사까지 가 주세요. 정문으로 들어가면 사거리가 나오는데, 거기에서 왼쪽으로 가시면 돼요. 가다 보면 도서관이 나와요. 도서관을 지나서 조금 가면 오른쪽에 작은 길이 있어요. 그 길로 조금 가면 왼쪽에 기숙사가 있어요. 그 앞에서 내려 주세요.','춤 경연 대회가 얼마 남지 않았어요. 민수 씨와 친구들은 땀을 흘리며 열심히 대회를 준비했어요. 드디어 대회 날이 되었어요. 무대에 올라가기 전에 민수 씨와 친구들은 다른 팀의 공연을 보면서 무척 긴장을 했어요. 하지만 무대에 올라가고 나서 민수 씨 팀은 하나도 떨지 않고 정말 멋있게 춤을 췄어요. 사람들도 소리를 지르며 즐거워했어요. 경연이 모두 끝난 후에 시상식을 했는데 민수 씨 팀이 1등을 했어요. 친구들은 정말 기뻐했고 민수 씨도 너무 좋아서 눈물이 났어요.','안내문을 설치해도 문제가 해결될 것 같지는 않아요. 아이들은 안내문을 잘 읽지 않고, 또 놀이터에는 글을 잘 모르는 어린 아이들도 많이 오잖아요. 놀이터는 아이들이 안전하고 즐겁게 뛰어놀 수 있는 곳이어야 된다고 생각해요. 그렇기 때문에 아이들에게 위험할 수 있는 운동 기구를 놀이터에 설치하는 건 안 좋은 것 같아요. 어른들을 위한 운동 기구는 놀이터가 아닌 다른 장소에 설치하면 좋겠어요.','인터넷 금융 거래 이용률이 2010년 25퍼센트에서 2020년 60퍼센트로 크게 증가하면서 은행 지점을 이용하는 사람은 10년 동안 천 개 이상  줄었습니다.','리더는 구성원들이 자발적, 의욕적으로 역량을 발휘할 수 있도록 환경을 조성해주는 것입니다.']

    total_score = {'similarity':0, 'pronunciation':0, 'fluency':0,'expression':0,'relevance':0}

    # 파이어베이스 Storage에서 데이터 가져오기 
    for i in range(1):

        # Storage에서 mp3 파일 다운받기
        part_url_name = 'part' + str(i + 1) + '_url'
        # storage_audio_path = request.form[part_url_name]
        storage_audio_path = 'User/b7c86adca4794b96/' + 'No' + str(i + 1) + '_b7c86adca4794b96_20211126_075936_test.mp3'
        
        print(storage_audio_path)

        local_audio_path = './Audio/' + storage_audio_path[-45:]
        print(local_audio_path)
        storage.child(storage_audio_path).download(local_audio_path)

        print('download completed')
        # 채점하기
        part_score = member_test_score.evaluate(local_audio_path, answer_list[i], komoran)
        print(part_score)
        print('evaludate completed')

        #total_score['similarity'] += part_score['similarity']
        #total_score['pronunciation'] += part_score['pronunciation']
        #total_score['fluency'] += part_score['fluency']
        #total_score['expression'] += part_score['expression']
        #total_score['relevance'] += part_score['correlation']
    
    #result_score = str(total_score['similarity']/6) + ' ' + str(total_score['pronunciation']/6) + ' ' +  str(total_score['fluency']/6) + ' ' + str(total_score['expression']/6) + ' ' + str(total_score['relevance']/6)

    #return result_score
    return 'finished'

@app.route('/post',methods=["POST"])
def hello_post():
    android_id = request.form['android_id']
    test_type = request.form['test_or_verify']
    start_date = request.form['date_time']


    # 모의고사 점수내기
    member_test_score = score.Member_Test()
    answer_list = ['제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.','아니요, 기사님. 학교 안에 있는 기숙사까지 가 주세요. 정문으로 들어가면 사거리가 나오는데, 거기에서 왼쪽으로 가시면 돼요. 가다 보면 도서관이 나와요. 도서관을 지나서 조금 가면 오른쪽에 작은 길이 있어요. 그 길로 조금 가면 왼쪽에 기숙사가 있어요. 그 앞에서 내려 주세요.','춤 경연 대회가 얼마 남지 않았어요. 민수 씨와 친구들은 땀을 흘리며 열심히 대회를 준비했어요. 드디어 대회 날이 되었어요. 무대에 올라가기 전에 민수 씨와 친구들은 다른 팀의 공연을 보면서 무척 긴장을 했어요. 하지만 무대에 올라가고 나서 민수 씨 팀은 하나도 떨지 않고 정말 멋있게 춤을 췄어요. 사람들도 소리를 지르며 즐거워했어요. 경연이 모두 끝난 후에 시상식을 했는데 민수 씨 팀이 1등을 했어요. 친구들은 정말 기뻐했고 민수 씨도 너무 좋아서 눈물이 났어요.','안내문을 설치해도 문제가 해결될 것 같지는 않아요. 아이들은 안내문을 잘 읽지 않고, 또 놀이터에는 글을 잘 모르는 어린 아이들도 많이 오잖아요. 놀이터는 아이들이 안전하고 즐겁게 뛰어놀 수 있는 곳이어야 된다고 생각해요. 그렇기 때문에 아이들에게 위험할 수 있는 운동 기구를 놀이터에 설치하는 건 안 좋은 것 같아요. 어른들을 위한 운동 기구는 놀이터가 아닌 다른 장소에 설치하면 좋겠어요.','인터넷 금융 거래 이용률이 2010년 25퍼센트에서 2020년 60퍼센트로 크게 증가하면서 은행 지점을 이용하는 사람은 10년 동안 천 개 이상  줄었습니다.','리더는 구성원들이 자발적, 의욕적으로 역량을 발휘할 수 있도록 환경을 조성해주는 것입니다.']


    # 날짜, 시간 데이터 준비하기
    test_id = "test_" + start_date[1:]
    android_db_id = "android_" + android_id

    storage_audio_paths = ""

    total_score = {'similarity':0, 'pronunciation':0, 'fluency':0,'expression':0,'relevance':0}

    # 파이어베이스 Storage에서 데이터 가져오기 
    for i in range(6):

        # Storage에서 mp3 파일 다운받기
        part_url_name = 'part' + str(i + 1) + '_url'
        storage_audio_path = request.form[part_url_name]
        print(storage_audio_path)
        local_audio_path = './Audio/' + storage_audio_path[-45:]
        storage.child(storage_audio_path).download(local_audio_path)
        print(local_audio_path)
        # 채점하기
        #part_score = member_test_score.evaluate(local_audio_path, answer_list[i], komoran)
        #print(part_score)

        # 파트 id
        #part_id = "part_" + str(i)

        # # 안드스튜디오에서 다른 파트도 추가하면됨, 확인테스트도 봐야함
        #db.child("member").child(android_db_id).child(test_type).update({
        #    test_id : {
        #         part_id : {
        #             "similarity": part_score['similarity'],
        #             "pronunciation": part_score['pronunciation'],
        #             "fluency": part_score['fluency'],
        #             "expression": part_score['expression'],
        #             "relevance": part_score['correlation'],
        #             "url": storage_audio_path
        #         }
        #     }
        # })
        #total_score['similarity'] += part_score['similarity']
        #total_score['pronunciation'] += part_score['pronunciation']
        #total_score['fluency'] += part_score['fluency']
        #total_score['expression'] += part_score['expression']
        #total_score['relevance'] += part_score['correlation']
    
    #result_score = str(total_score['similarity']/6) + ' ' + str(total_score['pronunciation']/6) + ' ' +  str(total_score['fluency']/6) + ' ' + str(total_score['expression']/6) + ' ' + str(total_score['relevance']/6)

    #return result_score
    return {'correlation': 10, 'expression': 10, 'fluency': 10, 'pronunciation': 0, 'similarity': 0}



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
