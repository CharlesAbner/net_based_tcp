import pymysql
import sys

class LogInformation(object):
    """
    数据库交互类，提供静态方法处理用户信息和头像。
    （已修复 SQL 注入漏洞，并改进错误处理）
    """

    # --- 数据库连接配置 (建议移到配置文件中) ---
    DB_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "1234", # 请替换为您的真实密码
        "db": "python_chat",
        "charset": "utf8mb4", # 推荐使用 utf8mb4 以支持 emoji 等
        "cursorclass": pymysql.cursors.DictCursor # (可选) 让 fetchone 返回字典
    }

    @staticmethod
    def _get_connection():
        """(内部辅助) 建立数据库连接"""
        try:
            return pymysql.connect(**LogInformation.DB_CONFIG)
        except pymysql.Error as e:
            print(f"数据库连接失败: {e}")
            # 在关键操作失败时可以抛出异常，让调用者知道
            raise ConnectionError(f"无法连接到数据库: {e}") from e

    @staticmethod
    def login_check(user_name, password):
        """
        检查用户登录凭据。
        修复了 SQL 注入漏洞。
        返回: True (成功), False (失败或出错)
        """
        db = None # 初始化连接变量
        try:
            db = LogInformation._get_connection()
            with db.cursor() as cursor:
                # 使用参数化查询防止 SQL 注入
                sql = "SELECT password FROM user_information WHERE user_name = %s"
                cursor.execute(sql, (user_name,))
                result = cursor.fetchone() # result 会是 {'password': 'xxx'} 或 None

                if result and password == result['password']: # 使用 DictCursor 后用键名访问
                    print(f"用户 '{user_name}' 登录验证成功。")
                    return True
                else:
                    print(f"用户 '{user_name}' 登录验证失败。")
                    return False
        except pymysql.Error as e:
            print(f"login_check 数据库错误: {e}")
            return False
        except ConnectionError: # 捕获 _get_connection 抛出的错误
             return False # 连接失败自然无法登录
        finally:
            if db:
                db.close()

    @staticmethod
    def create_new_user(user_name, password, file_name):
        """
        创建新用户，存储用户名、密码和头像。
        使用了参数化查询防止 SQL 注入。
        返回: "0" (成功), "1" (用户已存在), "2" (其他错误)
        """
        db = None
        img_data = None

        # 1. 检查用户名是否已存在 (先做这个可以避免不必要的文件读取)
        #    这里复用了 select_user_name 的逻辑，也可以直接在这里查
        if LogInformation.select_user_name(user_name) == "1":
             return "1" # 用户已存在

        # 2. 读取头像文件
        try:
            # 确保 file_name 非空且有效
            if not file_name:
                print("错误：未提供头像文件路径。")
                return "2" # 或者可以允许没有头像？取决于设计
            with open(file_name, 'rb') as fp:
                img_data = fp.read()
        except FileNotFoundError:
            print(f"错误：头像文件未找到: {file_name}")
            return "2"
        except IOError as e:
            print(f"错误：读取头像文件时出错: {e}")
            return "2"

        # 3. 插入数据库
        try:
            db = LogInformation._get_connection()
            with db.cursor() as cursor:
                # 使用参数化查询
                sql = "INSERT INTO user_information (user_name, password, data) VALUES (%s, %s, %s)"
                args = (user_name, password, img_data)
                cursor.execute(sql, args)
            db.commit() # 提交事务
            print(f"用户 '{user_name}' 创建成功。")
            return "0"
        except pymysql.IntegrityError:
             # 虽然前面检查过，但并发情况下仍可能插入重复，这里再捕获一次
             print(f"数据库错误：用户 '{user_name}' 可能已存在 (IntegrityError)。")
             if db: db.rollback() # 回滚
             return "1" # 返回用户已存在
        except pymysql.Error as e:
            print(f"create_new_user 数据库错误: {e}")
            if db: db.rollback() # 回滚
            return "2" # 其他数据库错误
        except ConnectionError:
             return "2" # 连接错误
        finally:
            if db:
                db.close()

    @staticmethod
    def select_user_name(user_name):
        """
        检查用户名是否已存在。
        修复了 SQL 注入漏洞。
        返回: "1" (存在), "0" (不存在), "2" (查询出错)
        """
        db = None
        try:
            db = LogInformation._get_connection()
            with db.cursor() as cursor:
                # 使用参数化查询，只查询是否存在即可，更高效
                sql = "SELECT 1 FROM user_information WHERE user_name = %s LIMIT 1"
                cursor.execute(sql, (user_name,))
                result = cursor.fetchone()

                if result:
                    # print(f"用户名 '{user_name}' 已存在。")
                    return "1"
                else:
                    # print(f"用户名 '{user_name}' 可用。")
                    return "0"
        except pymysql.Error as e:
            print(f"select_user_name 数据库错误: {e}")
            return "2" # 表示查询出错
        except ConnectionError:
             return "2" # 连接错误
        finally:
            if db:
                db.close()

    @staticmethod
    def find_face(user_name, output_filename='用户头像.png'):
        """
        根据用户名查找头像数据，并保存到本地文件。
        修复了 SQL 注入漏洞，移除了 sys.exit()。
        返回: True (成功找到并写入), False (用户不存在、无头像或出错)
        """
        db = None
        try:
            db = LogInformation._get_connection()
            with db.cursor() as cursor:
                # 使用参数化查询，只选择头像数据
                sql = "SELECT data FROM user_information WHERE user_name = %s"
                cursor.execute(sql, (user_name,))
                result = cursor.fetchone() # result = {'data': b'xxxxx'} 或 None

                if result and result['data']:
                    # 找到用户且头像数据存在
                    try:
                        with open(output_filename, 'wb') as fout:
                            fout.write(result['data'])
                        print(f"用户 '{user_name}' 的头像已保存到 {output_filename}")
                        return True
                    except IOError as e:
                        print(f"错误：写入头像文件时出错: {e}")
                        return False # 文件写入失败
                else:
                    print(f"用户 '{user_name}' 不存在或没有头像数据。")
                    return False # 用户不存在或无头像
        except pymysql.Error as e:
            print(f"find_face 数据库错误: {e}")
            return False # 数据库查询失败
        except ConnectionError:
             return False # 连接错误
        finally:
            if db:
                db.close()