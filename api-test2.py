# -*- coding:utf-8 -*-
#import urllib3
import json
import base64
import requests
import time
start = time.time()

#openApiURL = "http://aiopen.etri.re.kr:8000/WiseASR/Pronunciation"  # 영어
openApiURL = "http://aiopen.etri.re.kr:8000/WiseASR/PronunciationKor" # 한국어

accessKey = "ac679469-fbf1-4b08-abd7-f2aba1757ae6"
audioFilePath = "Audio/001_034.pcm"
languageCode = "korean"
#script = "PRONUNCIATION_SCRIPT"

file = open(audioFilePath, "rb")
audioContents = base64.b64encode(file.read()).decode("utf8")
file.close()

requestJson = {
    "access_key": accessKey,
    "argument": {
        "language_code": languageCode,
        #"script": script,
        "audio": audioContents
    }
}

#http = urllib3.PoolManager()
#response = http.request(
#    "POST",
#    openApiURL,
#    headers={"Content-Type": "application/json; charset=UTF-8"},
#    body=json.dumps(requestJson)
#)

response = requests.post( openApiURL,
                          data = json.dumps(requestJson),
                          headers={"Content-Type": "application/json; charset=UTF-8"}
)

y = response.json()

user = y["return_object"]['recognized']
score = y["return_object"]['score']
print(user,score)
print("time :", time.time() - start)  # 현재시각 - 시작시간 = 실행 시간