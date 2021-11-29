from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from nltk.probability import FreqDist
import requests
from pydub import AudioSegment

# 발음평가 api 불러올 때 필요
import urllib3
import json
import base64


class Member_Test:
    def __init__(self):
        self.test_type = "test"

    # raw data 추출을 위한 전처리
    def processing_audio(self,audioFilePath):

        audio_segment = AudioSegment.from_file(audioFilePath)  # audio 파일을 ms단위로 분해
        audio_segment = audio_segment.set_frame_rate(16000)  # sampling rate 16000으로 설정
        audio_segment = audio_segment.set_channels(1)  # channel을 1로 설정

        return audio_segment

    # 침묵 구간을 측정
    @staticmethod
    def get_silence(user_answer, threshold, interval):

        # audio를 interval기준으로 into chunks로 분리
        # interval 1이면 1 m/s
        chunks = [user_answer[i:i + interval] for i in range(0, len(user_answer), interval)]

        # dBFS는 어떤 오디오 시스템이 클립핑(Clipping)이 발생하기 직전까지 사용할 수 있는 최대 신호의 크기
        # 임계값 보다 낮은 dBFS을 침묵 구간으로 측정
        silence_length = 0
        for chunk in chunks:
            if chunk.dBFS == float('-inf') or chunk.dBFS < threshold:
                silence_length += 1

        return silence_length

    @staticmethod
    def myrange(start, end, step):
        r = start
        while(r<end):
            yield r
            r += step

    # 유창성 평가
    def score_fluency(self, audio_segment):
        threshold = -80
        interval = 1
        user_silence = Member_Test.get_silence(audio_segment, threshold, interval)  # 사용자의 침묵 시간

        sec_rate = round(user_silence / len(audio_segment) * 100)
        rate_list = [i for i in range(33, 101, 1)]  # 침묵 시간 비율
        score_list = [round(s) for s in Member_Test.myrange(0, 100, round(100 / 67, 2))]
        score_list.reverse()
        score_dict = dict(zip(rate_list, score_list))  # 점수로 변환할 딕셔너리

        # 말한 시간의 침묵이 1/3정도는 사람이 듣기에 유창하므로 1/3보다 정적이 적으면 만점
        if sec_rate < 33:
            score = 100
        else:
            score = score_dict[sec_rate]

        return score

    # 음성 분해
    def segment(self, audio_segment, interval=5000):
        print('segment start')
        chunks = [audio_segment[i:i + interval] for i in range(0, len(audio_segment), interval)]
        #rawdatas = [chunk.raw_data for chunk in chunks]
        print('chunks 통과')
        audioContents = []

        for chunk in chunks:
            rawdata = chunk.raw_data  # raw 데이터 추출
            audiocontent = base64.b64encode(rawdata).decode("utf8")  # 인코딩
            audioContents.append(audiocontent)

        return audioContents

    # 발음평가 API 사용
    @staticmethod
    def API(audioContent, script=None):

        openApiURL = "http://aiopen.etri.re.kr:8000/WiseASR/PronunciationKor"
        accessKey = "ac679469-fbf1-4b08-abd7-f2aba1757ae6"
        languageCode = "korean"
        requestJson = {
            "access_key": accessKey,
            "argument": {
                "language_code": languageCode,
                #    "script" : script,
                "audio": audioContent
            }
        }

        http = urllib3.PoolManager()
        response = http.request(
            "POST",
            openApiURL,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            body=json.dumps(requestJson)
        )
        print('pass 1')

        js = response.data
        y = json.loads(js)
        user = y["return_object"]['recognized']
        score = y["return_object"]['score']

        return user, score

    # 발음 평가
    def score_pronunciation(self, audioContents):

        user_answer = ''
        final_score = 0

        for audioContent in audioContents:
            user, score = Member_Test.API(audioContent)

            if user:
                user_answer += user
                final_score += score

        final_score = round(final_score / len(audioContents)) * 20

        return user_answer, final_score

    # 토크나이징
    def tokenizing(self, tokenizer, text):
        token = []
        all_token = []

        for sent in text.split('.'):
            morph = tokenizer.morphs(sent)
            if morph:
                token.append(morph)
                all_token += morph

        tagged = tokenizer.pos(text)
        nouns = [word for word, pos in tagged if pos in ['NNG', 'NNP']]

        return token, nouns, all_token

    # 키워드 추출
    def keyword(self, nouns):
        fdist = FreqDist(nouns)
        most_common = [token for token, freq in fdist.most_common(3)]

        return most_common

    # 단어의 표현을 측정
    def expression(self, text, token, all_token):
        text_len = len(text)  # 답안 길이
        word_len = len(set(all_token))  # 중복 제외 단어 수

        # 토크나이징된 리스트에 대한 각 길이를 저장
        word_len_list = [len(t) for t in token]
        sent_len = len(token) # 5초 길이 텍스트 수
        avg_len = sum(word_len_list) // sent_len  # 5초 당 평균 단어 수

        return {'text_len': text_len, 'word_len': word_len, 'avg_len': avg_len}

    # 표현력 채점
    def score_expression(self, user_dict, answer_dict):
        text_len = round(user_dict['text_len'] / answer_dict['text_len'] * 100)
        word_len = round(user_dict['word_len'] / answer_dict['word_len'] * 100)
        avg_len = round(user_dict['avg_len'] / answer_dict['avg_len'] * 100)

        score = round((0.15 * text_len) + 0.35 * (word_len + avg_len))

        if score > 100:  # 사용자가 모범답안보다 문장,단어를 더 풍부하게 사용한 경우
            score = 100

        return score

    # 텍스트 유사도 함수
    @staticmethod
    def text_similarity(user_all_token, answer_all_token):
        user = ' '.join(user_all_token)
        answer = ' '.join(answer_all_token)
        sent = (user, answer)
        count_vectorizer = CountVectorizer()
        count_matrix = count_vectorizer.fit_transform(sent)
        distance = cosine_similarity(count_matrix[0:1], count_matrix[1:2])[0][0] * 100

        return round(distance)

    # 모범 답안 유사도 평가
    def score_similarity(self,user_all_token, user_nouns, answer_all_token, answer_nouns):
        all_sim = Member_Test.text_similarity(user_all_token, answer_all_token)
        nouns_sim = Member_Test.text_similarity(user_nouns, answer_nouns)

        return (all_sim + nouns_sim) // 2

    # 주제의 연관성 평가
    def score_relevance(self,answer_keyword, user_keyword):
        url = 'http://3.145.8.27:5000/word2vec'
        score = requests.get(url, json={'answer': answer_keyword, 'user': user_keyword})
        #score = Member_Test.text_similarity(user_keyword, answer_keyword)
        if score:
            return score.json()
        else:
            score = Member_Test.text_similarity(user_keyword, answer_keyword)
            return score


    def evaluate(self, audio_file, answer, komoran):
        #try:
        audio_segment = self.processing_audio(audio_file)
        audioContents = self.segment(audio_segment, interval=5000)
    
        user, score = self.score_pronunciation(audioContents)
        print('채점 완료')
        return {'correlation': 0, 'expression': 0, 'fluency': 0, 'pronunciation': 0, 'similarity': 0}
            #user_token, user_nouns, user_all_token = self.tokenizing(komoran, user)
            #answer_token, answer_nouns, answer_all_token = self.tokenizing(komoran, answer)
            #user_dict = self.expression(user, user_token, user_all_token)
            #answer_dict = self.expression(answer, answer_token, answer_all_token)

            #answer_keyword = self.keyword(answer_nouns)
            #user_keyword = self.keyword(user_nouns)

            #flu = self.score_fluency(audio_segment)
            #pro = score
            #exp = self.score_expression(user_dict, answer_dict)
            #sim = self.score_similarity(user_all_token, user_nouns, answer_all_token, answer_nouns)
            #rel = self.score_relevance(answer_keyword, user_keyword)

            #return dict(zip(['fluency', 'pronunciation', 'expression', 'similarity', 'correlation'], [flu, pro, exp, sim, rel]))
#        except:
 #           print('채점 실패')
  #          return {'correlation': 0, 'expression': 0, 'fluency': 0, 'pronunciation': 0, 'similarity': 0}



import time

start = time.time()
from konlpy.tag import Komoran

komoran = Komoran()
answer = '제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.'
fname = '/home/ubuntu/flask-android-ec2/Audio/KOR_F_RM0769FLJH0325.mp3'

# 모의고사 점수내기
member_test_score = Member_Test()
print(member_test_score.evaluate(fname,answer,komoran))

print("time :", time.time() - start)  # 현재시각 - 시작시간 = 실행 시간
'''
def hello_get():

    # 모의고사 점수내기
    member_test_score = Member_Test()
    answer_list = ['제 취미는 영화보기에요.저는 시간있을 때 영화관에 가요. 재미있는 영화를 봐요.']

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

hello_get()
'''
