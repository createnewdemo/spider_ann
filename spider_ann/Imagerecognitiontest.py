import json
import re

import requests



url = 'http://150.158.170.46:8089/api/tr-run/'
img1_file = {
    'file': open('test.jpg', 'rb')
}
response = requests.post(url=url, data={'compress': 0,'is_draw':0}, files=img1_file)
response.encoding='utf-8'
raw_out = response.json()['data']['raw_out']
# 数据解析：图片地址+图片名称
recognized_str = ''
for code in enumerate(raw_out):
    recognized_str += code[1][1] + '\n'
print(recognized_str)

