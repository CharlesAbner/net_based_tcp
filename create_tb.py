import pymysql
Connection = pymysql.connect(host="localhost", user="root", password="1234", db="python_chat")
cursor = Connection.cursor()
sql_create_table = ''' create table user_information ( user_name varchar (20), password varchar (20), data MEDIUMBLOB ) '''
cursor.execute(sql_create_table)
cursor.close()