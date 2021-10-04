from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from konlpy.tag import Komoran
from nltk.probability import FreqDist
from gensim.models import Word2Vec
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
        chunks = [audio_segment[i:i + interval] for i in range(0, len(audio_segment), interval)]
        rawdatas = [chunk.raw_data for chunk in chunks]

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
        word_len = sum(word_len_list)  # 총 단어 수

        # 0으로 나누는 거 방지 -> 코드 고치기
        if sent_len == 0:
            sent_len = 1
        avg_len = word_len // sent_len  # 5초 당 평균 단어 수

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
    def score_relevance(self,model, answer_keyword, user_keyword):
        sim_list = []

        for a in answer_keyword:
            for u in user_keyword:
                try:
                    sim_list.append(model.wv.similarity(a, u))
                except KeyError:
                    pass

        key_sim = Member_Test.text_similarity(user_keyword, answer_keyword)

        # 0으로 나누는 거 방지 -> 코드 고치기
        if len(sim_list) == 0:
            len_sim_list = 1
        else:
            len_sim_list = len(sim_list)
        score = round((sum(sim_list) / len_sim_list) * 50 + (key_sim * 0.5))

        return score

    def evaluate(self, audio_file, answer):
        audio_segment = self.processing_audio(audio_file)
        audioContents = self.segment(audio_segment, interval=5000)

        

        user, score = self.score_pronunciation(audioContents)
        komoran = Komoran()                   # 로드하는데 오래걸리니까 main.py에서 처리할 것
        model = Word2Vec.load('model/ko.bin') # 로드하는데 오래걸리니까 main.py에서 처리할 것

        

        user_token, user_nouns, user_all_token = self.tokenizing(komoran, user)
        answer_token, answer_nouns, answer_all_token = self.tokenizing(komoran, answer)
        user_dict = self.expression(user, user_token, user_all_token)
        answer_dict = self.expression(answer, answer_token, answer_all_token)

        

        answer_keyword = self.keyword(answer_nouns)
        user_keyword = self.keyword(user_nouns)

        return "점수 계산 완료"

        flu = self.score_fluency(audio_segment)
        pro = score
        exp = self.score_expression(user_dict, answer_dict)
        sim = self.score_similarity(user_all_token, user_nouns, answer_all_token, answer_nouns)
        rel = self.score_relevance(model, answer_keyword, user_keyword)

        return dict(zip(['유창성', '발음평가', '표현력', '유사도', '주제의 연관성'], [flu, pro, exp, sim, rel]))





