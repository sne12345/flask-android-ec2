import requests
import time

start = time.time()
url = 'http://15.165.31.148:5000/score'
answer = '올림픽 축구 대표팀이 내일 청소년 축구 대표팀과 평가전을'
fname = '/home/ubuntu/flask-android-ec2/Audio/KOR_F_RM0769FLJH0325.mp3'
r = requests.get(url, json={'fname':fname,'answer': answer})
print(r)
if r:
    r = r.json()
print(r)
print("time :", time.time() - start)  # 현재시각 - 시작시간 = 실행 시간
