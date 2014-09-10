name: inverse
layout: true

---
class: title, center, middle, inverse

노래만 나오는 라디오
# <span class="sky">방</span>금 <span class="sky">그</span>  <span class="sky">라</span>디오
.footnote[
- [onairradio](https://www.facebook.com/pages/%EB%B0%A9%EA%B8%88%EA%B7%B8%EB%9D%BC%EB%94%94%EC%98%A4/760855817307720) on FaceBook
- [onairradio](https://github.com/dubu/onairradio) on GitHub
- [onairradio](https://github.com/dubu/onairradio) on YouTube
]


---
class: center, middle, inverse, full-text
.full-image[![](IMG_20140910_130116.jpg)]

---
class: center, middle, inverse, full-text

".gold[라디오 노래]만 듣고 싶다.<br>
.gold[광고]는 안듣고 싶은데..<br>
노래 골라들으며 안되나요<br>
노래만 듣고 싶다."

.pull-right[-- 노래만 듣고 싶은이]

---
class: center, middle, inverse, full-text

".gold[감사합니다.] 방송국 작가분들에 선곡에 감사합니다.<br>
.gold[좋네요]좋은노래들 많이 나옵니다.<br>
티비에는 아이돌 노래만 나오는데 골고루 좋은 노래들<br>
하루 종일 틀어 놓아도 좋아요"

---

class: middle, inverse, full-text
# 준비물

1. [방금그곡api](http://music.daum.net/onair/timeline)
1. python3
1. raspberry pi
1. [Nokia 5110 LCD](http://www.devicemart.co.kr/31029)
1. [스피커](http://www.10x10.co.kr/shopping/category_prd.asp?itemid=898765&rdsite=nvshop_sp&NaPm=ct%3Dhzw68blk%7Cci%3Dd6f9db6ebddfcf32f6bd366d6b80154138ec0cdd%7Ctr%3Dsl%7Csn%3D219718%7Chk%3D69a0516a1216cf93849a469bda19f1d5330d3df7)
1. [빵판](http://www.devicemart.co.kr/32298)
1. 스위치
1. [점퍼케이블](http://www.devicemart.co.kr/32284)

---
class: center, middle, inverse, full-text

# 선연결
.full-image[![](IMG_20140910_130116.jpg)]

---

class: middle, inverse, full-text

시간이 좀 남았나요?

---
class:  middle, inverse, full-text

# 방금그라디오 소스
- [onair.py source](https://github.com/onairradio/onairradio.github.io/blob/master/onair.py)

    ```python
    ....
    url = 'http://music.daum.net/onair/songlist.json?type=top&searchDate='
    resp = requests.post(url=url)
    data = json.loads(resp.text)

    while True:
        if isHolding:
            lcd.cls()
            lcd.text("Hold")
        if GPIO.input(14) == 1 and old_val == 0:
            print("Button 1 pressed")
            isHolding = not isHolding
            old_val = 1
            time.sleep(1)
        else :
            old_val = 0

        playList = []
        if time.time() - t > 10 :
            t = time.time()
            print("refresh")
            resp = requests.post(url=url)
            data = json.loads(resp.text)

            for song in reversed(data['songList']):
                if song['channel']['channelType'] != "4" or  song['channel']['channelName'] in  ["KBS 3라디오", "MBC FM4U"]:
                    continue
    ...
    ```

---
class:  middle, inverse, full-text
# 작업

- pcd8544 Python library 설치 https://github.com/XavierBerger/pcd8544
- pil 라이브러리 python2 에서만 실행.
- python3 사용하기 위해 Pillow lib 설치.http://pillow.readthedocs.org/en/latest/installation.html
- 각종 에러가 발생하는데 lcd.py 적절히 수정해 준다.
- 한글폰트 설치 sudo apt-get install ttf-unfonts-core
- 그 밖에 각종 설치
    ```python
    sudo pip-3.2 install wiringpi
    sudo pip-3.2 install wiringpi2
    sudo pip-3.2 install spidev
    sudo pip-3.2 install spidev
    sudo pip-3.2 install Pillow
    ```
---
class:  middle, inverse, full-text
# 몇 가지 트릭

- 한글 romanize하기

    ```python
    >>> from unidecode import unidecode
    >>> unidecode(u'파이콘')
    'paikon'
    ```

- 한자, 한글, 영문가 섞여 있는 경우

    - Multilingual NLP에서 제안하는 다양한 접근법이 있습니다.
    - 간단한 꼼수 한 가지는: "한자 전처리, 영문 후처리"
        - 한자는 transliterate하고 (ex: '丁新闻' -> 정신문)
        - 한국어 처리를 한 후에 (ex: POS tagging)
        - 영문으로 분류된 tag에 한해 따로 stemming 등을 거침

---
class: center, middle, inverse, full-text

감사합니다 ^_^

http://onairradio.github.io<br>
kozazz@hanmail.net


