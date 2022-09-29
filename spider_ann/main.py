import re
import time
import os
import requests
import pytesseract
from PIL import Image
from lxml import etree
import datetime
import pymysql
from pymysql.converters import escape_string
import math
from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler(daemon=True)
class ccgp_Central():
    def __init__(self):
        self.screenshot_dir = os.path.join(os.path.dirname(__file__),r"screenshots")
        if not os.path.exists(self.screenshot_dir):
            os.mkdir(self.screenshot_dir)
    def gen_sql(self,table_name, data):
        """
        　　:param table_name: 表名称
        　　:param data: 字典对象 key为字段(要与数据库字段一样), value为插入值
        　　:return: 拼接好的sql语句
        """
        fields = list()
        values = list()
        for k, v in data.items():
            if v:  # 没有值, 就不插入
                fields.append(k)
                values.append(v)
        fields_count = len(fields)
        f = "(" + "{}," * (fields_count - 1) + "{})"
        v = "(" + "\"{}\"," * (fields_count - 1) + "\"{}\")"
        #v = "(" + "\'{}\'," * (fields_count - 1) + "\'{}\')"
        sql = """insert into {} """ + f + """ VALUES """ + v
        sql = sql.format(table_name, *fields, *values)
        return sql
    def convertToBinaryData(self,filename):#返回图片字节流
        # Convert digital data to binary format
        with open(filename, 'rb') as file:
            binaryData = file.read()
        return binaryData
    def insert_database(self,sql):
        self.conn = pymysql.connect(
            host='rm-8vbj0khvttjk3n8tuno.mysql.zhangbei.rds.aliyuncs.com',
            port=3306,
            user='xxcj',
            password='123456',
            database='xxcj'
        )
        # 创建游标
        cursor = self.conn.cursor()
        try:
            cursor = self.conn.cursor()
            result = cursor.execute(sql)
            print('------------------------本次存入数据中为数据库中第'+str(cursor.lastrowid)+'条数据------------------------------------')  # 获取自增的ID值
            #print(result)  # result是该sql会影响多少条数据
            self.conn.commit()  # 提交
        except Exception as e:
            print('------------------------------------本次存入数据失败------------------------------------')  # 获取自增的ID值
            print(e)
            self.conn.rollback()  # 回滚
        cursor.close()  # 断开cursor
        self.conn.close()  # 断开连接 #插入数据表
    def located_recognize_text(self,image_path):#本地识别
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'  # 这个放上自己安装的exe的路径就可以
        tessdata_dir_config = r'--tessdata-dir "C:\Program Files (x86)\Tesseract-OCR\tessdata"'  # 这个也是自己安装的路径，这个tessdata也在那个安装目录下
        image = Image.open(image_path)
        # 图片路径
        code = pytesseract.image_to_string(image, config=tessdata_dir_config,lang='chi_sim')
        print(code)
    def remote_recognize_text(self):
        try:
            url = 'http://150.158.170.46:8089/api/tr-run/'
            img1_file = {
                'file': open('screenshots/test.jpg', 'rb')
            }
            response = requests.post(url=url, data={'compress': 0, 'is_draw': 0}, files=img1_file)
            response.encoding = 'utf-8'
            raw_out = response.json()['data']['raw_out']
            # 数据解析：图片地址+图片名称
            recognized_str = ''
            for code in enumerate(raw_out):
                recognized_str += code[1][1]
            #recognized_str.replace('\n','')
        except Exception as e:
            print('识别返回失败')
            print(e)
            recognized_str = ''
        return recognized_str
    def download_pic_and_recognize(self,id):
        headers = {
            'authority': 'www.plap.cn',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        }
        data = {
            'id': id,
        }
        response = requests.post('https://www.plap.cn/index/downloadDetailsImage.html',headers=headers, data=data, stream=True)
        with open('screenshots/test.jpg', 'wb') as f:
            f.write(response.content)
        with open('screenshots/test.jpg', 'rb') as file_byte:
            file_hex = file_byte.read().hex()
        #img_content = pymysql.Binary(response.content)
        #print(img_content)
        return self.remote_recognize_text(),file_hex
    def spider_data1(self):#军队采购网采购公告
        first_url = "https://www.plap.cn/index/selectAllByTabs.html"
        headers = {
            'authority': 'www.plap.cn',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        }
        params = {
            "articleTypeId": "1",
            "secondArticleTypeId": "2",
            "publishStartDate": str(datetime.datetime.now()).split(" ")[0],
            "publishEndDate": str(datetime.datetime.now()).split(" ")[0],
        }
        response = requests.get(first_url,headers=headers,params=params)
        page_regx = 'pages: "(.*?)"'
        total_regx = 'total: "(.*?)"'
        pages = re.findall(page_regx,response.text)[0]
        total = re.findall(total_regx,response.text)[0]
        print('------------------------------------军队采购网采购公告今日更新%s页，一共%s条数据----------------------------'% (pages,total))
        index = 1
        for page in range(1,int(pages)+1):
            print('---------------------------------------开始采集第%d页------------------------------------------'%(page))
            params = {
                "articleTypeId": "1",
                "secondArticleTypeId": "2",
                "publishStartDate": str(datetime.datetime.now()).split(" ")[0],
                "publishEndDate": str(datetime.datetime.now()).split(" ")[0],
                "page":page
            }
            response = requests.get(first_url, headers=headers, params=params)
            tree = etree.HTML(response.text)
            li_list = tree.xpath('//*[@class="report_list_box"]/ul/li')
            for li in li_list:
                #局部解析
                href = 'https://www.plap.cn/'+li.xpath('./a/@href')[0]
                if self.find_history(href) == 1:
                    print("----------------------------------------本条信息今日已经被记录，不进行存储------------------------------")
                    time.sleep(0.2)
                    continue
                self.write_history(url=href)
                id = href.split('=')[1]
                recognized_content,original_content = self.download_pic_and_recognize(id)
                title = li.xpath('./a/@title')[0]
                product_type = li.xpath('./span[1]//text()')[0]
                post_time = li.xpath('./span[2]//text()')[0]
                collection_time = datetime.datetime.now()
                callection_category = '军队采购网采购公告'
                region = ''
                purchaser= ''
                data_dict= {
                    'title':title,
                    'product_type':product_type,
                    'post_time':post_time,
                    'original_content':original_content,
                    'recognized_content':recognized_content,
                    'collection_time':collection_time,
                    'callection_category':callection_category,
                    'region':region,
                    'purchaser':purchaser,
                    'href':href,
                }
                sql = self.gen_sql('bidding_information', data_dict)

                self.insert_database(sql)
                print(f'-----------------------第{index}条数据--{title}--采集入库完成--------------')
                index += 1
            print('----------------------------------------------------第%d页采集完成-------------------------------------------------' % (page))
        pass
        #self.located_recognize_text(filename)
    def spider_data2(self):#军队采购网信息公告
        first_url = "https://www.plap.cn/index/selectAllByTabs.html"
        headers = {
            'authority': 'www.plap.cn',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        }
        params = {
            "articleTypeId": "1",
            "secondArticleTypeId": "23",
            "publishStartDate": str(datetime.datetime.now()).split(" ")[0],
            "publishEndDate": str(datetime.datetime.now()).split(" ")[0],
        }
        response = requests.get(first_url,headers=headers,params=params)
        page_regx = 'pages: "(.*?)"'
        total_regx = 'total: "(.*?)"'
        pages = re.findall(page_regx,response.text)[0]
        total = re.findall(total_regx,response.text)[0]
        print('----------------------------------------军队采购网信息公告今日更新%s页，一共%s条数据-----------------------------'% (pages,total))
        index = 1
        for page in range(1,int(pages)+1):
            print('-----------------------------------------------------开始采集第%d页-----------------------------------------------------'%(page))
            params = {
                "articleTypeId": "1",
                "secondArticleTypeId": "23",
                "publishStartDate": str(datetime.datetime.now()).split(" ")[0],
                "publishEndDate": str(datetime.datetime.now()).split(" ")[0],
                "page":page
            }
            response = requests.get(first_url, headers=headers, params=params)
            tree = etree.HTML(response.text)
            li_list = tree.xpath('//*[@class="report_list_box"]/ul/li')
            for li in li_list:
                #局部解析
                href = 'https://www.plap.cn/'+li.xpath('./a/@href')[0]
                if self.find_history(href) == 1:
                    print("----------------------------------------本条信息今日已经被记录，不进行存储------------------------------")
                    time.sleep(0.2)
                    continue
                self.write_history(url=href)
                id = href.split('=')[1]
                recognized_content,original_content = self.download_pic_and_recognize(id)

                title = li.xpath('./a/@title')[0]
                product_type = li.xpath('./span[1]//text()')[0]
                post_time = li.xpath('./span[2]//text()')[0]
                collection_time = datetime.datetime.now()
                callection_category = '军队采购网信息公告'
                region = ''
                purchaser= ''
                data_dict= {
                    'title':title,
                    'product_type':product_type,
                    'post_time':post_time,
                    'original_content':original_content,
                    'recognized_content':recognized_content,
                    'collection_time':collection_time,
                    'callection_category':callection_category,
                    'region':region,
                    'purchaser':purchaser,
                    'href':href,
                }
                sql = self.gen_sql('bidding_information', data_dict)

                self.insert_database(sql)
                print(f'-----------------------第{index}条数据--{title}--采集入库完成--------------')
                index += 1
            print('----------------------------------------------------第%d页采集完成-------------------------------------------------' % (page))
        pass
        #self.located_recognize_text(filename)
    def spider_data3(self):#武器装备采购信息网采购公告
        first_url = "http://www.weain.mil.cn/api/front/list/cggg/list"
        headers = {
            'Referer': 'http://www.weain.mil.cn/cggg/jdgg/list.shtml',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        }
        params = {
            "LMID": "1149231276155707394",
            "pageNo": "1",
            "startTime": str(datetime.datetime.now()).split(" ")[0],
            "endTime": str(datetime.datetime.now()).split(" ")[0],
        }
        response = requests.get(first_url, headers=headers, params=params)
        data_json = response.json()
        totalNum = data_json["list"]["totalNum"]
        pageNum = math.ceil(float(totalNum)/20)#向下取整 得到页码
        #print(pageNum)
        print('----------------------武器装备采购信息网采购公告今日更新%s页，一共%s条数据------------------------------------' % (pageNum, totalNum))
        index = 1
        for page in range(1,pageNum+1):
            print('------------------------------------开始采集第%d页------------------------------------'%(page))
            params = {
                "LMID": "1149231276155707394",
                "pageNo": page,
                "startTime": str(datetime.datetime.now()).split(" ")[0],
                "endTime": str(datetime.datetime.now()).split(" ")[0],
            }
            response = requests.get(first_url, headers=headers, params=params)
            data_json = response.json()
            contentList = data_json["list"]["contentList"]
            for content in contentList:
                #post_time = content["publishTime"] #可入库
                ID = content["ID"]
                href = 'http://www.weain.mil.cn/' + content["pcUrl"]#可入库
                if self.find_history(href) == 1:
                    print("----------------------------------------本条信息今日已经被记录，不进行存储------------------------------")
                    time.sleep(0.2)
                    continue
                self.write_history(url=href)
                deadline = content["deadline"]
                type = content["type"]
                title = content["nonSecretTitle"]  #可入库
                purchaseType = content["purchaseType"]
                secretGrade = content["secretGrade"]
                LMID = content["LMID"]
                response = requests.get(href,headers=headers, params=params)
                response.encoding = 'utf-8'
                regx = 'id=\"publicType\" value=\"(.*?)\">'
                msg = re.findall(regx,response.text)[0]
                if msg == '2':
                    print("------------------------------------权限不够！不采集！------------------------------------")
                    #print(title, href)
                elif msg == '1':
                    print("------------------------------------可以查看,进行采集！------------------------------------")
                    tree = etree.HTML(response.content)
                    product_type = tree.xpath('//*[@id="majorField"]/@title')[0]
                    post_time = tree.xpath('//*[@id="created"]/text()')[0].strip()
                    #recognized_content = tree.xpath('//*[@id="content"]')
                    content_ele = tree.xpath('//*[@id="content"]/text()')[0]
                    con_regx = '<p>(.*?)</p>'
                    # purchaser_regx = '<p>联.*?：(.*?)</p><p>(.*?)</p>'
                    # region_regx = '<p>地.*?址：(.*?)</p>'
                    con_list = re.findall(con_regx,content_ele)
                    # purchaser_list = re.findall(purchaser_regx,content_ele)
                    # print(purchaser_list)
                    # # purchaser = purchaser_list[0][0]+'-----'+purchaser_list[0][1]  #可入库
                    # try:
                    #     region = re.findall(region_regx,content_ele)[0] #可入库
                    #     # print(purchaser.replace('&nbsp;',''))
                    #     print(region)
                    # except Exception as e:
                    #     print("无地址")
                    recognized_content = ''
                    for con in con_list:
                        #可入库
                        recognized_content += con.replace('<strong>','').replace('</strong>','').replace('&nbsp;','').replace('<a>','').replace('</a>','').replace('<br/>','') + '\n'
                    collection_time = datetime.datetime.now()
                    callection_category = '武器装备采购信息网采购公告'
                    data_dict = {
                        'title': title,
                        'product_type': product_type,
                        'post_time': post_time,
                        'original_content': '',
                        'recognized_content': recognized_content,
                        'collection_time': collection_time,
                        'callection_category': callection_category,
                        'region': '',
                        'purchaser': '',
                        'href': href,
                    }
                    sql = self.gen_sql('bidding_information', data_dict)
                    self.insert_database(sql)
                    print(f'--------------------第{index}条数据--{title}--采集入库完成------------------------------------')
                    index += 1
            print('------------------------------------第%d页采集完成------------------------------------' % (page))
    def spider_data4(self):#武器装备采购信息网采购需求
        first_url = "http://www.weain.mil.cn/api/front/list/cgxq/list"
        headers = {
            'Referer': 'http://www.weain.mil.cn/cgxq/jdxq/list.shtml',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        }
        params = {
            "LMID": "HZ287281676ce46401676cf0975c000e",
            "pageNo": "1",
            "startTime": str(datetime.datetime.now()).split(" ")[0],
            "endTime": str(datetime.datetime.now()).split(" ")[0],
        }
        response = requests.get(first_url, headers=headers, params=params)
        data_json = response.json()
        totalNum = data_json["list"]["totalNum"]
        pageNum = math.ceil(float(totalNum)/20)#向下取整 得到页码
        #print(pageNum)
        print('--------------------------武器装备采购信息网采购需求今日更新%s页，一共%s条数据----------------------' % (pageNum, totalNum))
        index = 1
        for page in range(1,pageNum+1):
            print('-----------------------------开始采集第%d页----------------------------------------'%(page))
            params = {
                "LMID": "HZ287281676ce46401676cf0975c000e",
                "pageNo": page,
                "startTime": str(datetime.datetime.now()).split(" ")[0],
                "endTime": str(datetime.datetime.now()).split(" ")[0],
            }
            response = requests.get(first_url, headers=headers, params=params)
            data_json = response.json()
            contentList = data_json["list"]["contentList"]
            for content in contentList:
                #post_time = content["publishTime"] #可入库
                #ID = content["ID"]
                href = 'http://www.weain.mil.cn/' + content["pcUrl"]#可入库
                if self.find_history(href) == 1:
                    print("----------------------------------------本条信息今日已经被记录，不进行存储------------------------------")
                    time.sleep(0.2)
                    continue
                self.write_history(url=href)
                #deadline = content["deadline"]
                #type = content["type"]
                title = content["nonSecretTitle"]  #可入库
                #purchaseType = content["purchaseType"]
                #secretGrade = content["secretGrade"]
                #LMID = content["LMID"]
                source_response = requests.get(href,headers=headers, params=params)
                source_response.encoding = 'utf-8'
                tree = etree.HTML(source_response.text)
                product_type = tree.xpath('//*[@id="demandProjectType"]/text()')[0]
                post_time = tree.xpath('//*[@id="demandPublishTime"]/text()')[0].strip()
                con_regx = 'HtmlUtil.htmlDecode\(\'(.*?)\'\)\);'
                # purchaser_regx = '<p>联.*?：(.*?)</p><p>(.*?)</p>'
                # region_regx = '<p>地.*?址：(.*?)</p>'
                recognized_content = re.findall(con_regx,source_response.text)[0]
                collection_time = datetime.datetime.now()
                callection_category = '武器装备采购信息网采购公告'
                data_dict = {
                    'title': title,
                    'product_type': product_type,
                    'post_time': post_time,
                    'original_content': '',
                    'recognized_content': recognized_content,
                    'collection_time': collection_time,
                    'callection_category': callection_category,
                    'region': '',
                    'purchaser': '',
                    'href': href,
                }
                sql = self.gen_sql('bidding_information', data_dict)
                self.insert_database(sql)
                print(f'-----------------------第{index}条数据--{title}--采集入库完成--------------')
                index += 1
            print('------------------------------------第%d页采集完成------------------------------------' % (page))
    def spider_data5(self):#政府采购网采购中央单位采购公告  政府采购网采购地方单位采购公告
        first_url = "http://search.ccgp.gov.cn/bxsearch"
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        }
        params = {
            'searchtype': '1',
            'page_index': '1',
            'bidSort': '0',
            'buyerName': '',
            'projectId': '',
            'pinMu': '0',
            'bidType': '',
            'dbselect': 'bidx',
            'kw': '',
            'start_time': str(datetime.datetime.now()).split(" ")[0].replace("-",":"),
            'end_time': str(datetime.datetime.now()).split(" ")[0].replace("-",":"),
            'timeType': '0',
            'displayZone': '',
            'zoneId': '',
            'pppStatus': '0',
            'agentName': '',
        }
        response = requests.get(first_url,headers=headers,params=params)
        #print(first_url)
        response.encoding='utf-8'
        source_txt =response.text
        nums_regx = "c00000\">(.*?)<\/span>"
        page_regx = 'Pager([\s\S]*?),'#匹配换行和空格
        totalNum = re.findall(nums_regx,source_txt)[0]
        pageNum = re.findall(page_regx,source_txt)[0].replace(" ",'').split(':')[1]
        index = 1
        print('-----------------政府采购网今日更新%s页，一共%s条数据---------------------' % (pageNum, totalNum))
        for page in range(1,int(pageNum)+1):
            print('--------------------------开始采集第%d页--------------------------------' % (page))
            params = {
                'searchtype': '1',
                'page_index': page,
                'bidSort': '0',
                'buyerName': '',
                'projectId': '',
                'pinMu': '0',
                'bidType': '',
                'dbselect': 'bidx',
                'kw': '',
                'start_time': str(datetime.datetime.now()).split(" ")[0].replace("-",":"),
                'end_time': str(datetime.datetime.now()).split(" ")[0].replace("-",":"),
                'timeType': '0',
                'displayZone': '',
                'zoneId': '',
                'pppStatus': '0',
                'agentName': '',
            }
            page_response = requests.get(first_url, headers=headers, params=params,allow_redirects=False)
            tree = etree.HTML(page_response.text)
            c_list_bid = tree.xpath('//ul[@class="vT-srch-result-list-bid"]//li') #每页20个
            for li in c_list_bid:
                href = li.xpath('./a/@href')[0]
                if self.find_history(href) == 1:
                    print("----------------------------------------本条信息今日已经被记录，不进行存储------------------------------")
                    time.sleep(0.2)
                    continue
                self.write_history(url=href)
                title = li.xpath('./a/text()')[0].strip()
                post_time = li.xpath('./span/text()')[0].split('|')[0].strip()
                purchaser = li.xpath('./span/text()')[0].split('|')[1].strip()
                try:
                    region = li.xpath('./span/a/text()')[0].strip()
                except Exception as e:
                    region = ''
                collection_time = datetime.datetime.now()
                detail_response = requests.get(href, headers=headers, params=params)
                detail_response.encoding = 'utf-8'
                detail_source_txt = detail_response.content
                tree = etree.HTML(detail_source_txt)
                #time.sleep(5)
                #noticeArea = tree.xpath('//div[@class="vF_detail_content_container"]')[0].xpath('string(.)')
                #p_list = tree.xpath('//div[@class="vF_detail_content"]//p')
                all_attr_list = tree.xpath('//div[@class="vF_detail_content"]//descendant::*')
                recognized_content = ''
                for attr in all_attr_list:
                    if attr.tag == 'script':
                        continue
                    if attr.tag == 'blockquote' or attr.tag == 'p' or attr.tag == 'table' or attr.tag == 'b':
                        recognized_content += attr.xpath('string(.)')

                recognized_content = recognized_content.replace("function.*?;}}","").replace("function Toggle(id) { if (document.getElementById(id).style.display == 'none') { document.getElementById(id).style.display = 'block'; } else { document.getElementById(id).style.display = 'none';}}","")
                callection_category = '政府采购网采购中央单位采购公告 政府采购网采购地方单位采购公告'
                data_dict = {
                    'title': title,
                    'product_type': '',
                    'post_time': post_time,
                    'original_content': '',
                    'recognized_content': recognized_content,
                    'collection_time': collection_time,
                    'callection_category': callection_category,
                    'region': region,
                    'purchaser': purchaser,
                    'href': href,
                }
                sql = self.gen_sql('bidding_information', data_dict)
                self.insert_database(sql)
                index += 1
                print(f'-----------------------第{index}条数据--{title}--采集入库完成--------------')
            print( '--------------------------------------第%d页采集完成------------------------------------' % (page))
    def write_history(self,url):
        file = open('history.txt', 'a+')
        file.seek(0)
        file.write(url + '\n')
        file.close()
    def find_history(self,url):
        history_url_list=[]
        file = open('history.txt', 'r')
        for line in file.readlines():
            history_url_list.append(line.strip())
        if  url  in history_url_list:
            return 1
        else:
            return 0

    def distroy_history(self):
        with open("history.txt", 'r+') as file:
            file.truncate(0)

    def login(self):
        pass


    def main(self):#主函数
        self.spider_data1()
        self.spider_data2()
        self.spider_data3()
        self.spider_data4()
        self.spider_data5()

    # def run_on_time(self):  # 定时执行
    #     sched.start()
    #     pass


def run():
    ccgp_Central().main()
def distroy():
    ccgp_Central().distroy_history()
    print("已清理")
print('---------------------开启定时程序------------------------')
sched.add_job(run, 'cron', hour='12,22', minute=0)
sched.add_job(distroy, 'cron',  hour='0', minute=0)
print('---------------------定时程序 等待运行------------------------')
sched.start()
