import socket
import threading
import math
import time # 用于调试或日志

# --- 全局变量 ---
online_connections = list()       # 存储所有活跃的客户端 socket 连接
connection_user = dict()        # 存储 socket 连接 -> 用户名的映射
flag_new_user_joined = 0        # 特殊标记：1 表示 handle_message 需要广播加入消息
connections_lock = threading.Lock() # ！！！【重要】线程锁，用于保护对全局列表和字典的访问

# --- 协议相关的辅助函数 ---

def send_string_with_length(conn, content):
    """
    发送带有4字节长度前缀的字符串 (UTF-8编码)。
    """
    try:
        encoded_content = content.encode('utf-8')
        length = len(encoded_content)
        conn.sendall(length.to_bytes(4, byteorder='big'))
        conn.sendall(encoded_content)
    except (socket.error, BrokenPipeError, OSError) as e:
        print(f"Error sending string: {e}")
        # 在实际应用中可能需要更复杂的错误处理，比如标记连接失效

def send_number(conn, number):
    """
    发送一个4字节的整数。
    """
    try:
        conn.sendall(int(number).to_bytes(4, byteorder='big'))
    except (socket.error, BrokenPipeError, OSError) as e:
        print(f"Error sending number: {e}")

def recv_all_string(connection):
    """
    接收带有4字节长度前缀的完整字符串。
    如果连接关闭或出错，返回 None。
    """
    try:
        # 1. 接收长度 (信封)
        length_bytes = connection.recv(4)
        if not length_bytes: # 对方关闭了连接
            return None
        length = int.from_bytes(length_bytes, byteorder='big')

        # 2. 循环接收数据，直到收够 length 字节 (信纸)
        chunks = []
        bytes_received = 0
        while bytes_received < length:
            # 计算还需要多少字节，但最多只接收缓冲区大小
            bytes_to_recv = min(length - bytes_received, 2048) # 一次最多收 2k
            chunk = connection.recv(bytes_to_recv)
            if not chunk: # 连接在接收过程中意外断开
                raise ConnectionError("Connection closed unexpectedly during recv")
            chunks.append(chunk)
            bytes_received += len(chunk)

        # 3. 拼接并解码
        full_data = b''.join(chunks)
        return full_data.decode('utf-8')

    except (socket.error, ConnectionError, ValueError, OSError) as e: # ValueError for int.from_bytes if data is bad
        print(f"Error receiving string: {e}")
        return None # 返回 None 表示接收失败

# --- 数据库交互占位符 ---
try:
    from chat_db import LogInformation
except ImportError:
    print("错误：无法导入 chat_mysql.py。请确保该文件在同一目录下。")

def check_user(user_name, password):
    """
    检查用户名和密码是否匹配。
    调用 chat_mysql.LogInformation.login_check。
    成功返回 True, 失败或出错返回 False。
    """
    print(f"[DB Check] 正在检查用户 '{user_name}' 的登录...")
    try:
        # 直接调用 chat_mysql 中的静态方法
        result = LogInformation.login_check(user_name, password)
        print(f"[DB Check] 用户 '{user_name}' 登录结果: {result}")
        return result # login_check 已经返回 True 或 False
    except Exception as e:
        # 捕获 LogInformation.login_check 中可能未处理的异常
        print(f"[DB Check] 调用 login_check 时发生意外错误: {e}")
        return False

def add_user(user_name, password, file_name):
    """
    添加新用户到数据库。
    调用 chat_mysql 中的 select_user_name 和 create_new_user。
    返回: "0" (成功), "1" (用户已存在), "2" (其他错误)。
    """
    print(f"[DB Add] 正在尝试添加用户 '{user_name}'...")
    try:
        # 1. 先检查用户名是否存在
        check_exist_result = LogInformation.select_user_name(user_name)

        if check_exist_result == "1":
            print(f"[DB Add] 用户名 '{user_name}' 已存在。")
            return "1"
        elif check_exist_result == "2":
            print(f"[DB Add] 检查用户名 '{user_name}' 时发生数据库错误。")
            return "2"
        elif check_exist_result == "0":
            # 用户名可用，尝试创建
            print(f"[DB Add] 用户名 '{user_name}' 可用，尝试创建...")
            create_result = LogInformation.create_new_user(user_name, password, file_name)
            print(f"[DB Add] 创建用户 '{user_name}' 结果: {create_result}")
            return create_result # create_new_user 会返回 "0" 或 "1" 或 "2"
        else:
            # select_user_name 返回了意外的值
            print(f"[DB Add] select_user_name 返回了未知结果: {check_exist_result}")
            return "2"

    except Exception as e:
        # 捕获 LogInformation 方法中可能未处理的异常
        print(f"[DB Add] 调用数据库方法时发生意外错误: {e}")
        return "2"

# --- 核心处理函数 ---

def broadcast_online_list():
    """
    【线程安全】向所有在线用户广播当前的在线列表。
    """
    # 使用锁保护全局列表和字典的访问
    with connections_lock:
        current_connections = list(online_connections) # 创建副本以防迭代时列表改变
        num_online = len(current_connections)
        user_names = [connection_user[conn] for conn in current_connections if conn in connection_user]

    print(f"Broadcasting online list to {num_online} users: {user_names}")
    # 遍历副本进行发送
    for conn in current_connections:
        try:
            send_string_with_length(conn, "#!onlinelist#!") # 特殊标记
            send_number(conn, num_online)
            for name in user_names:
                send_string_with_length(conn, name)
        except Exception as e:
            print(f"Error broadcasting list to a client: {e}")
            # 如果发送失败，可能需要移除这个连接，但这通常在 handle 线程的 finally 中处理

def handle_login(connection, address):
    """
    处理登录请求 (Type "1")。
    成功返回 True, 失败返回 False (并关闭连接)。
    """
    global flag_new_user_joined # 声明要修改全局变量

    name = recv_all_string(connection)
    if name is None: return False # 接收出错或连接断开
    password = recv_all_string(connection)
    if password is None: return False

    print(f"[{address}] Attempting login: User='{name}'")

    check_result = check_user(name, password)

    if check_result:
        connection.sendall(b"1") # 回复登录成功标记
        
        # 使用锁来安全地修改全局变量
        with connections_lock:
            # 检查用户名是否已在线 (防止重复登录)
            for conn, user in connection_user.items():
                if user == name:
                    print(f"[{address}] Login failed: User '{name}' already online.")
                    connection.sendall(b"2") # 发送特定错误码，例如 "2" 代表已登录
                    return False # 登录失败，关闭连接

            # 添加到在线列表和用户名字典
            online_connections.append(connection)
            connection_user[connection] = name
            print(f"[{address}] Login successful: User='{name}' added.")
            
            # 设置特殊标记，准备广播加入消息
            flag_new_user_joined = 1

        # 触发一次用户列表广播 (这个函数内部会处理锁)
        broadcast_online_list()

        # 触发一次"加入"消息广播 (这个函数内部也会处理锁和flag)
        handle_message(connection, address, is_join_broadcast=True) # 传递特殊参数

        return True # 登录成功，保持连接
    else:
        print(f"[{address}] Login failed: Invalid credentials for User='{name}'.")
        connection.sendall(b"0") # 回复登录失败标记
        return False # 登录失败，将在 finally 中关闭连接

def handle_register(connection, address):
    """
    处理注册请求 (Type "2")。
    处理完后返回 True (保持连接让用户看到结果)。
    """
    name = recv_all_string(connection)
    if name is None: return False
    password = recv_all_string(connection)
    if password is None: return False
    file_name = recv_all_string(connection) # 头像文件名
    if file_name is None: return False

    print(f"[{address}] Attempting register: User='{name}'")

    result_code = add_user(name, password, file_name)
    connection.sendall(result_code.encode('utf-8')) # 直接回复数据库操作结果码
    
    print(f"[{address}] Register result for User='{name}': Code={result_code}")
    
    # 注册后通常保持连接，让客户端显示结果，然后客户端可以尝试登录
    return True # 保持连接

def handle_message(connection, address, is_join_broadcast=False):
    """
    处理消息发送请求 (Type "3") 或登录成功后的加入广播。
    处理完后返回 True (保持连接)。
    """
    global flag_new_user_joined # 声明要修改/读取全局变量

    sender_name = None
    # 先安全地获取发送者用户名
    with connections_lock:
        sender_name = connection_user.get(connection) # 使用 get 防止 KeyError

    if not sender_name:
        print(f"[{address}] Error: Received message from unknown/unlogged user.")
        # 可能需要发送错误信息或直接断开
        return False # 或者 True? 取决于设计，这里先断开

    # --- 情况1：处理登录成功后的“加入”广播 ---
    if flag_new_user_joined and is_join_broadcast:
        content = f'* 系统提示: {sender_name} 加入聊天室'
        print(f"Broadcasting join message: {content}")
        
        # 使用锁保护广播过程
        with connections_lock:
            current_connections = list(online_connections) # 创建副本
            for c in current_connections:
                try:
                    send_string_with_length(c, "#!message#!")
                    send_string_with_length(c, "group_chat") # 系统消息按群聊处理
                    send_string_with_length(c, sender_name) # “发送者”是加入者
                    send_string_with_length(c, content)
                except Exception as e:
                    print(f"Error broadcasting join message to a client: {e}")
            
            # 广播完成后，重置标记
            flag_new_user_joined = 0 
        
        return True # 广播完成，保持连接

    # --- 情况2：处理客户端发来的普通聊天消息 ---
    elif not is_join_broadcast:
        chat_target = recv_all_string(connection) # 接收聊天对象 ("【群聊】" 或 用户名)
        if chat_target is None: return False
        content = recv_all_string(connection) # 接收消息内容
        if content is None: return False

        print(f"[{address}] Message from '{sender_name}' to '{chat_target}': {content}")
        # 使用锁保护广播/私聊过程
        with connections_lock:
            current_connections = list(online_connections) # 创建副本
            
            # --- 群聊逻辑 ---
            if chat_target == "【群聊】":
                for c in current_connections:
                    # (可选：可以不发给自己) if c == connection: continue
                    try:
                        send_string_with_length(c, "#!message#!")
                        send_string_with_length(c, "group_chat")
                        send_string_with_length(c, sender_name)
                        send_string_with_length(c, content)
                    except Exception as e:
                         print(f"Error broadcasting group message to a client: {e}")

            # --- 私聊逻辑 ---
            else:
                target_found = False
                # 寻找私聊目标
                for c in current_connections:
                    if c in connection_user and connection_user[c] == chat_target:
                        target_found = True
                        try:
                            # 发给目标
                            send_string_with_length(c, "#!message#!")
                            send_string_with_length(c, "private_chat")
                            send_string_with_length(c, sender_name)
                            send_string_with_length(c, content)
                            
                            # 同时回发给自己
                            if connection != c: # 避免自己给自己发两次
                                send_string_with_length(connection, "#!message#!")
                                send_string_with_length(connection, "private_chat")
                                send_string_with_length(connection, sender_name) # 发送者是自己
                                send_string_with_length(connection, content)
                                
                        except Exception as e:
                             print(f"Error sending private message: {e}")
                        break # 找到目标就不用再找了
                
                # 如果没找到私聊目标
                if not target_found:
                    try:
                        # 可以给发送者一个提示
                        send_string_with_length(connection, "#!system#!") # 定义一个新的系统提示标记
                        send_string_with_length(connection, f"用户 '{chat_target}' 不在线或不存在。")
                    except Exception as e:
                        print(f"Error sending 'user not found' notice: {e}")

        return True # 消息处理完成，保持连接
    else:
        # flag=0 但 is_join_broadcast=True 的情况不应发生
        print("Warning: Inconsistent state in handle_message.")
        return True

# --- 客户端处理总入口 (运行在每个子线程中) ---

def handle(connection, address):
    """
    每个客户端连接的主处理循环。
    """
    print(f"[新连接] 来自 {address} 的连接已建立。")
    client_name = None # 用于日志和退出广播
    try:
        while True:
            # 1. 接收请求类型 (阻塞)
            request_type_bytes = connection.recv(1) # 假设类型用1字节
                                                   
            if not request_type_bytes:
                print(f"[提示] {address} 主动断开 (收到空类型)。")
                break # 客户端关闭连接
            # (如果用数字类型)
            # request_type_int = int.from_bytes(request_type_bytes, byteorder='big')
            # request_type = str(request_type_int)
            # (如果用短字符串类型，需要修改发送端)
            request_type = request_type_bytes.decode('utf-8').strip() # strip() 去掉可能的空白
            if not request_type: # 防止空字符串类型
                 print(f"[警告] {address} 发送了空请求类型。")
                 continue # 继续等待下一个请求
            print(f"[{address}] Received request type: '{request_type}'")
            # 2. 根据类型分发任务
            keep_going = True
            if request_type == "1":   # 登录
                keep_going = handle_login(connection, address)
                # 登录成功后记录用户名，用于退出广播
                if keep_going:
                     with connections_lock:
                         client_name = connection_user.get(connection)
            elif request_type == "2": # 注册
                keep_going = handle_register(connection, address)
            elif request_type == "3": # 发送消息
                 keep_going = handle_message(connection, address)
            elif request_type == "4": # 刷新列表 (客户端主动请求)
                broadcast_online_list() # 直接调用广播函数即可
                keep_going = True # 刷新列表后保持连接
            else:
                print(f"[警告] {address} 发送了未知请求类型: '{request_type}'")
                # 可以选择忽略或断开
                keep_going = True # 暂时忽略

            # 3. 如果处理函数要求断开连接
            if not keep_going:
                break

    except (socket.error, ConnectionResetError, OSError) as e:
        print(f"[异常] {address} 连接异常: {e}")
        # 异常退出循环

    finally:
        # --- 核心清理逻辑 ---
        print(f"[断开连接] 清理来自 {address} 的连接...")
        
        # 使用锁保护全局列表和字典的修改
        with connections_lock:
            # a. 从在线列表中移除 (如果存在)
            if connection in online_connections:
                online_connections.remove(connection)
                print(f"    从 online_connections 移除。")
            
            # b. 从用户名字典中移除 (如果存在) 并获取用户名
            removed_user = connection_user.pop(connection, None) # 安全移除
            if removed_user:
                client_name = removed_user # 确保拿到用户名
                print(f"    从 connection_user 移除用户 '{client_name}'。")

        # c. 关闭 socket 连接 (在锁之外操作socket)
        try:
            connection.close()
            print(f"    Socket 连接已关闭。")
        except Exception as e:
            print(f"    关闭 socket 时发生异常: {e}")

        # d. 广播用户离开消息 (如果用户已登录)
        if client_name:
            print(f"    广播用户 '{client_name}' 离开消息...")
            # 构造离开消息
            content = f'* 系统提示: {client_name} 已离开群聊'
            # 再次加锁广播
            with connections_lock:
                current_connections = list(online_connections) # 创建副本
                for c in current_connections:
                    try:
                        send_string_with_length(c, "#!message#!")
                        send_string_with_length(c, "group_chat") # 系统消息按群聊处理
                        send_string_with_length(c, client_name) # “发送者”是离开者
                        send_string_with_length(c, content)
                    except Exception as e:
                        print(f"    广播离开消息时出错: {e}")
            # 广播最新的用户列表
            broadcast_online_list()

        print(f"[清理完成] {address} 的线程结束。")

# --- 服务器主入口 ---

if __name__ == "__main__":
    HOST = '127.0.0.1'  # 监听本地所有接口可用 '0.0.0.0'
    PORT = 12345        # 您选择的端口号

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 设置地址重用，这样服务器重启时可以立刻绑定端口
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(10) # 最大等待连接数
        print(f"服务器启动成功，正在监听 {HOST}:{PORT} ...")
        while True:
            # 阻塞等待新连接
            connection, client_address = server_socket.accept()
            # 为新连接启动一个处理线程
            client_thread = threading.Thread(
                target=handle,
                args=(connection, client_address),
                daemon=True # 设置为守护线程，主线程退出时子线程也强制退出
            )
            client_thread.start()

    except Exception as e:
        print(f"服务器主线程出错: {e}")
    finally:
        print("服务器正在关闭...")
        server_socket.close()
        # (可以添加更优雅的关闭逻辑，比如通知所有在线用户)