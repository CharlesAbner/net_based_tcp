import socket
import math
import sys # 用于退出

class ChatSocket:
    """
    封装了与聊天服务器进行通信的底层 socket 操作和协议细节。
    """
    def __init__(self, server_host='127.0.0.1', server_port=12345):
        """
        初始化客户端 socket 并连接到服务器。
        """
        print("初始化 TCP 客户端...")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (server_host, server_port)
        try:
            self.client_socket.connect(self.server_address)
            print(f"成功连接到服务器 {server_host}:{server_port}")
        except ConnectionRefusedError:
            print(f"错误：无法连接到服务器 {server_host}:{server_port}。服务器未运行或地址错误。")
            # 在实际应用中，这里可能需要重试或直接退出程序
            sys.exit(1) # 直接退出
        except socket.error as e:
            print(f"连接服务器时发生 socket 错误: {e}")
            sys.exit(1)

    # --- 高级动作函数 (给 Controller 调用) ---

    def login_type(self, user_name, password):
        """
        发送登录请求 (类型 "1") 并获取服务器响应。
        返回: "1" (成功), "0" (失败), 或 None (发生错误)。
        """
        try:
            self.client_socket.sendall(b"1") # 发送类型码 "1"
            self.send_string_with_length(user_name)
            self.send_string_with_length(password)
            check_result = self.recv_string_by_length(1) # 接收 1 字节的响应码
            return check_result
        except Exception as e:
            print(f"发送登录请求时出错: {e}")
            return None

    def register_user(self, user_name, password, file_name):
        """
        发送注册请求 (类型 "2") 并获取服务器响应。
        返回: "0" (成功), "1" (用户已存在), "2" (其他错误), 或 None (发生错误)。
        """
        try:
            self.client_socket.sendall(b"2") # 发送类型码 "2"
            self.send_string_with_length(user_name)
            self.send_string_with_length(password)
            self.send_string_with_length(file_name if file_name else "") # 如果没选头像发空字符串
            check_result = self.recv_string_by_length(1) # 接收 1 字节的响应码
            return check_result
        except Exception as e:
            print(f"发送注册请求时出错: {e}")
            return None

    def send_message(self, message, chat_user):
        """
        发送聊天消息 (类型 "3")。不直接接收响应。
        返回: True (发送成功), False (发送失败)。
        """
        try:
            self.client_socket.sendall(b"3") # 发送类型码 "3"
            self.send_string_with_length(chat_user) # 发送聊天对象
            self.send_string_with_length(message)   # 发送消息内容
            return True
        except Exception as e:
            print(f"发送消息时出错: {e}")
            return False

    def send_refurbish_mark(self):
        """
        发送刷新在线用户列表请求 (类型 "4")。不直接接收响应。
        返回: True (发送成功), False (发送失败)。
        """
        try:
            self.client_socket.sendall(b"4") # 发送类型码 "4"
            return True
        except Exception as e:
            print(f"发送刷新列表请求时出错: {e}")
            return False

    # --- 底层协议辅助函数 ---

    def send_string_with_length(self, content):
        """
        【协议核心】发送带有4字节长度前缀的字符串 (UTF-8编码)。
        如果发送失败，会抛出异常。
        """
        try:
            encoded_content = content.encode('utf-8')
            length = len(encoded_content)
            self.client_socket.sendall(length.to_bytes(4, byteorder='big'))
            self.client_socket.sendall(encoded_content)
        except (socket.error, BrokenPipeError, OSError) as e:
            print(f"发送字符串时出错: {e}")
            raise # 将异常向上抛出，让调用者知道发送失败

    def send_number(self, number):
        """
        【协议核心】发送一个4字节的整数。
        如果发送失败，会抛出异常。
        """
        try:
            self.client_socket.sendall(int(number).to_bytes(4, byteorder='big'))
        except (socket.error, BrokenPipeError, OSError) as e:
            print(f"发送数字时出错: {e}")
            raise

    def recv_string_by_length(self, length):
        """
        【协议核心】接收固定长度的字符串。
        返回: 解码后的字符串, 或 None (连接关闭或出错)。
        """
        try:
            data_bytes = self.client_socket.recv(length)
            if not data_bytes:
                print("接收定长字符串时连接关闭。")
                return None
            return data_bytes.decode('utf-8')
        except (socket.error, ConnectionResetError, OSError) as e:
            print(f"接收定长字符串时发生 Socket 错误: {e}")
            return None
        except UnicodeDecodeError as e:
            print(f"接收定长字符串时解码错误: {e}")
            return None # 或者可以返回一个特定错误标记

    def recv_all_string(self):
        """
        【协议核心】接收带有4字节长度前缀的完整字符串。
        这是接收线程会反复调用的核心函数。
        返回: 解码后的字符串, 或 None (连接关闭或出错)。
        """
        try:
            # 1. 接收长度 (信封)
            length_bytes = self.client_socket.recv(4)
            if not length_bytes:
                print("接收变长字符串长度时连接关闭。")
                return None
            
            try:
                 length = int.from_bytes(length_bytes, byteorder='big')
            except ValueError:
                 print("接收变长字符串长度时数据格式错误。")
                 return None # 数据损坏

            # 防止超大长度导致内存问题 (可选)
            # if length > 10 * 1024 * 1024: # e.g., max 10MB
            #     print(f"错误：尝试接收过大的消息 ({length} bytes)")
            #     return None # 或者可以尝试消耗掉这些数据

            # 2. 循环接收数据 (信纸)
            chunks = []
            bytes_received = 0
            while bytes_received < length:
                bytes_to_recv = min(length - bytes_received, 4096) # 一次最多收 4k
                chunk = self.client_socket.recv(bytes_to_recv)
                if not chunk:
                    # 连接在接收数据中途断开
                    raise ConnectionError("连接在接收数据时意外关闭。")
                chunks.append(chunk)
                bytes_received += len(chunk)

            # 3. 拼接并解码
            full_data = b''.join(chunks)
            try:
                return full_data.decode('utf-8')
            except UnicodeDecodeError as e:
                print(f"接收变长字符串时解码错误: {e}")
                return None # 数据损坏

        except (socket.error, ConnectionError, ConnectionResetError, OSError) as e:
            print(f"接收变长字符串时发生 Socket 错误: {e}")
            return None # 连接问题

    def recv_number(self):
        """
        【协议核心】接收一个4字节的整数。
        返回: 整数, 或 None (连接关闭或出错)。
        """
        try:
            number_bytes = self.client_socket.recv(4)
            if not number_bytes:
                print("接收数字时连接关闭。")
                return None
            try:
                return int.from_bytes(number_bytes, byteorder='big')
            except ValueError:
                 print("接收数字时数据格式错误。")
                 return None # 数据损坏
        except (socket.error, ConnectionResetError, OSError) as e:
            print(f"接收数字时发生 Socket 错误: {e}")
            return None

    # --- 关闭连接 ---
    def close(self):
        """
        关闭客户端 socket 连接。
        """
        print("正在关闭客户端 socket...")
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR) # 优雅关闭
        except socket.error as e:
            print(f"关闭 socket 时出错 (shutdown): {e}") # 可能已经关闭
        finally:
            self.client_socket.close()
            print("客户端 socket 已关闭。")