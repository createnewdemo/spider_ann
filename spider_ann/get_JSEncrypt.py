import execjs
import requests
node = execjs.get()
fp = open('./wuqi.js','r',encoding='utf-8')
ctx = node.compile(fp.read().replace(u'\xa0',u' '))
funcName = 'logins()'
result = ctx.eval(funcName)
print(result)
Username = result[0]
Pwd = result[1]
def login():

    headers = {
        'Origin': 'http://www.weain.mil.cn',
        'Referer': 'http://www.weain.mil.cn/login.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'isEncrypt': 'isNotEncrypt',
    }

    json_data = {
        'userName': Username,
       'password': Pwd ,
        'signStr': '',
        'dn': '',
        'source': '',
        'loginMode': '100',
    }

    response = requests.post('http://www.weain.mil.cn/cg_unit/front/cgmember/login', headers=headers,
                             json=json_data, verify=False)
    print(response.text)
login()