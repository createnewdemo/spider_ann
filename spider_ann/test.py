import datetime

import pymysql


def insert_database(sql):
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='root',
        database='spider_data'
    )
    # 创建游标
    cursor = conn.cursor()
    try:
        cursor = conn.cursor()
        result = cursor.execute(sql)
        print('本次存入数据中为数据库中第' + str(cursor.lastrowid) + '条数据')  # 获取自增的ID值
        # print(result)  # result是该sql会影响多少条数据
        conn.commit()  # 提交
    except Exception as e:
        print('本次存入数据失败')  # 获取自增的ID值
        print(e)
        conn.rollback()  # 回滚
    cursor.close()  # 断开cursor
    conn.close()  # 断开连接 #插入数据表

def gen_sql(table_name, data):
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
    print(f)
    v = "(" + "\'{}\'," * (fields_count - 1) + "\'{}\')"
    print(v)
    sql = """insert into {} """ + f + """ VALUES """ + v
    sql = sql.format(table_name, *fields, *values)
    return sql


# with open('test.jpg', 'rb') as file_byte:
#     file_hex = file_byte.read().hex()

# sql = gen_sql('alldata',{'original_content':file_hex})
# print(sql)
# insert_database(sql)

# print(datetime.datetime.now())
# print(str(datetime.datetime.now()).split(" ")[0])
#
#
# def distroy_history():
#     with open("test.txt", 'r+') as file:
#         file.truncate(0)
# distroy_history()
file = open('history.txt', 'w')
file.write("dwadad" + '\n')

