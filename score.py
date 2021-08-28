from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from konlpy.tag import Komoran
from nltk.probability import FreqDist
from gensim.models import Word2Vec
from pydub import AudioSegment


class Member_Test:

    def __init__(self):
        self.test_type = "test"

    def get_silence(self, audio_file, threshold, interval):
        # audio 파일을 ms단위로 분해
        user_answer = AudioSegment.from_raw(
                              audio_file,
                              sample_width=4,
                              frame_rate= 4000,bitrate= 8000,
                              channels=2,
                            )

        # audio를 interval기준으로 into chunks로 분리
        # interval 1이면 1 m/s
        chunks = [user_answer[i:i + interval] for i in range(0, len(user_answer), interval)]

        # dBFS는 어떤 오디오 시스템이 클립핑(Clipping)이 발생하기 직전까지 사용할 수 있는 최대 신호의 크기
        # 임계값 보다 낮은 dBFS을 침묵 구간으로 측정
        silence_length = 0
        for chunk in chunks:
            if chunk.dBFS == float('-inf') or chunk.dBFS < threshold:
                silence_length += 1

        # 초 단위로 변환
        return round(silence_length * (interval / 1000))

    def myrange(self,start, end, step):
        r = start
        while(r<end):
            yield r
            r += step


    def score_fluency(self, audio, part_num):
        threshold = -80
        interval = 1
        user_silence = self.get_silence(audio, threshold, interval)  # 사용자의 침묵 시간
        part_second = {1: 30, 2: 40, 3: 60, 4: 60, 5: 80}  # 파트별 초 시간

        sec_rate = round(user_silence / part_second[part_num] * 100)  # 전체 시간 중 침묵 시간의 %
        rate_list = [i for i in range(33, 101, 1)]  # 침묵 시간 비율
        score_list = [round(s) for s in self.myrange(0, 100, round(100 / 67, 2))]
        score_list.reverse()
        score_dict = dict(zip(rate_list, score_list))  # 점수로 변환할 딕셔너리

        # 말한 시간의 침묵이 1/3정도는 사람이 듣기에 유창하므로 1/3보다 정적이 적으면 만점
        if sec_rate < 33:
            score = 100
        else:
            score = score_dict[sec_rate]

        return score


    def score_pronunciation(self):
        user = "제 취미는 영화 보기입니다. 저는 시간 있으면 영화관에 갑니다. 집에서도 영화를 가끔 봅니다. 저는 영화가 재밌어야 좋아해요. 슬픈 영화는 싫어해요. 저는 다음주 주말에 친구와 함께 영화관에 갈거예요."
        answer = "제 취미는 영화 보기예요. 저는 시간 있을 때 영화관에 가요. 집에서도 영화를 자주 봐요. 저는 재미있는 영화를 좋아해요. 슬픈 영화도 잘 봐요. 저는 이번 주말에 친구와 함께 영화관에 갈 거예요."
        score = 80
        return user, answer, score


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


    def keyword(self, nouns):
        fdist = FreqDist(nouns)
        most_common = [token for token, freq in fdist.most_common(3)]

        return most_common


    def expression(self, text, token, all_token):
        text_len = len(text)  # 답안 길이
        word_len = len(set(all_token))  # 중복 제외 단어 수

        # 토크나이징된 리스트에 대한 각 길이를 저장
        word_len_list = [len(t) for t in token]

        sent_len = len(token)  # 문장 수
        word_len = sum(word_len_list)  # 총 단어 수
        avg_len = word_len // sent_len  # 문장별 평균 단어 수

        return {'text_len': text_len, 'word_len': word_len, 'sent_len': sent_len, 'avg_len': avg_len}


    def score_expression(self, user_dict, answer_dict):
        text_len = round(user_dict['text_len'] / answer_dict['text_len'] * 100)
        word_len = round(user_dict['word_len'] / answer_dict['word_len'] * 100)
        sent_len = round(user_dict['sent_len'] / answer_dict['sent_len'] * 100)
        avg_len = round(user_dict['avg_len'] / answer_dict['avg_len'] * 100)

        score = round(0.3 * (text_len + sent_len) + 0.7 * (word_len + avg_len))

        if score > 100:  # 사용자가 모범답안보다 문장,단어를 더 풍부하게 사용한 경우
            score = 100

        return score


    def text_similarity(self, user_all_token, answer_all_token):
        user = ' '.join(user_all_token)
        answer = ' '.join(answer_all_token)
        sent = (user, answer)
        count_vectorizer = CountVectorizer()
        count_matrix = count_vectorizer.fit_transform(sent)
        distance = cosine_similarity(count_matrix[0:1], count_matrix[1:2])[0][0] * 100

        return round(distance)


    def score_similarity(self, user_all_token, user_nouns, answer_all_token, answer_nouns):
        all_sim = self.text_similarity(user_all_token, answer_all_token)
        nouns_sim = self.text_similarity(user_nouns, answer_nouns)

        return (all_sim + nouns_sim) // 2


    def score_relevance(self, model, answer_keyword, user_keyword):
        sim_list = []

        for a in answer_keyword:
            for u in user_keyword:
                try:
                    sim_list.append(model.wv.similarity(a, u))
                except KeyError:
                    pass

        key_sim = self.text_similarity(user_keyword, answer_keyword)
        score = round((sum(sim_list) / len(sim_list)) * 50 + (key_sim * 0.5))

        return score


    def evaluate(self, audio_file,part_num=1):
        user, answer, score = self.score_pronunciation()  # 아무렇게나 일단 만듦
        komoran = Komoran()
        model = Word2Vec.load('model/ko.bin')

        user_token, user_nouns, user_all_token = self.tokenizing(komoran, user)
        answer_token, answer_nouns, answer_all_token = self.tokenizing(komoran, answer)
        user_dict = self.expression(user, user_token, user_all_token)
        answer_dict = self.expression(answer, answer_token, answer_all_token)

        answer_keyword = self.keyword(answer_nouns)
        user_keyword = self.keyword(user_nouns)

        flu = self.score_fluency(audio_file, part_num)
        pro = score
        exp = self.score_expression(user_dict, answer_dict)
        sim = self.score_similarity(user_all_token, user_nouns, answer_all_token, answer_nouns)
        rel = self.score_relevance(model, answer_keyword, user_keyword)

        return dict(zip(['유창성', '발음평가', '표현력', '유사도', '주제의 연관성'], [flu, pro, exp, sim, rel]))
