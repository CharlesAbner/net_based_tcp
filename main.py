import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import threading
import time
import queue
import sys # For sys.exit

# 导入您自己编写的模块
try:
    from Login_panel import LoginPanel
    from Register_panel import RegisterPanel
    from main_panel import MainPanel
    from client import ChatSocket # 包含 ChatSocket 类
except ImportError as e:
    print(f"错误：无法导入必要的模块 - {e}")
    print("请确保 chat_login_panel.py, chat_register_panel.py, chat_main_panel.py, chat_client.py 文件存在于同一目录下。")
    sys.exit(1)

# --- 全局变量 ---
client = None          # ChatSocket 实例 (网络引擎)
login_frame = None     # LoginPanel 实例 (登录窗口)
register_frame = None  # RegisterPanel 实例 (注册窗口)
main_frame = None      # MainPanel 实例 (主聊天窗口)
chat_user = "【群聊】"  # 当前聊天对象，默认为群聊
is_running = True      # 控制接收线程的开关

# --- 辅助函数 ---

def close_socket():
    """安全地关闭 socket 连接"""
    global is_running
    is_running = False # 通知接收线程停止
    if client:
        print("尝试断开 socket 连接...")
        try:
            # (可选) 可以尝试发送一个退出消息给服务器
            # client.send_message("exit", "【群聊】") # 根据服务器协议决定
            client.close() # 调用 ChatSocket 的 close 方法
        except Exception as e:
            print(f"关闭 socket 时发生错误: {e}")

def close_login_window():
    """关闭登录窗口时的回调 (点 'X')"""
    print("关闭登录窗口...")
    close_socket()
    if login_frame:
        try:
            # login_frame.close_login_panel() # 调用 Panel 内部的 destroy
            # 或者直接销毁 (如果 Panel 没提供方法)
            login_frame.login_frame.destroy() 
        except Exception as e:
             print(f"销毁登录窗口时出错: {e}")
    # (如果需要完全退出程序)
    # sys.exit(0) 

def close_main_window():
    """关闭主聊天窗口时的回调 (点 'X' 或 '关闭' 按钮)"""
    print("关闭主聊天窗口...")
    if client and main_frame:
        # 发送退出标记给服务器 (根据服务器协议)
        # 注意：这里可能需要确保消息发送完成再关闭
        client.send_message("exit", chat_user) 
        # (可以加一小段延时 time.sleep(0.1) 确保发出)
    close_socket() 
    if main_frame:
        try:
            # main_frame.close_main_panel() # 如果 Panel 提供了方法
            main_frame.main_frame.destroy()
        except Exception as e:
             print(f"销毁主窗口时出错: {e}")
    # sys.exit(0)

def file_open_face():
    """处理 '添加头像' 按钮点击"""
    print("选择头像文件...")
    # 打开文件选择对话框
    # filetypes 可以限制可选的文件类型
    file_name = filedialog.askopenfilename(title="选择头像图片", 
                                           filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif")])
    if file_name:
        print(f"选择了头像文件: {file_name}")
        # 命令 RegisterPanel 更新头像显示
        if register_frame:
            register_frame.add_face(file_name)
    else:
        print("没有选择文件。")
        messagebox.showwarning(title="提示", message="您还没有选择文件！")

def private_talk(event): # 注意：bind 方法会传递一个 event 对象
    """处理在线用户列表点击事件"""
    global chat_user
    
    # 确保 main_frame 存在
    if not main_frame or not main_frame.friend_list:
        return
        
    widget = event.widget # 获取被点击的 Listbox 控件
    selection = widget.curselection() # 获取选中的行的索引元组

    if selection:
        index = selection[0] # 通常只选一行
        
        # 检查是否点击了有效区域 (避免点击标题行出错)
        if index >= 0: # 确保索引有效
             target = widget.get(index) # 获取选中的文本 (用户名或 "【群聊】")
             
             # 排除点击 "在线用户数:" 行
             if "在线用户数:" in target: 
                 return

             print(f"选择了聊天对象: {target}")
             
             if target == '【群聊】':
                 chat_user = '【群聊】'
                 title = f" 在线用户 python聊天室欢迎您：{main_frame.user_name} "
                 main_frame.change_title(title)
             elif target == main_frame.user_name: # 点击了自己
                 messagebox.showwarning(title="提示", message="不能和自己私聊!")
                 # (可以选择是否切回群聊)
                 # chat_user = '【群聊】' 
                 # title = f" 在线用户 python聊天室欢迎您：{main_frame.user_name} "
                 # main_frame.change_title(title)
             else: # 点击了其他用户
                 chat_user = target
                 title = f" 与 {chat_user} 私聊中... "
                 main_frame.change_title(title)
        else:
            print("未选中有效行")
    else:
         print("未选中任何行")


# --- 主要的回调处理函数 ---

def handding_login(login_panel_instance): # 参数是 LoginPanel 实例
    """处理登录按钮点击"""
    print("处理登录请求...")
    user_name, password = login_panel_instance.get_input()

    if not user_name:
        messagebox.showwarning(title="提示", message="用户名不能为空")
        return
    if not password:
        messagebox.showwarning(title="提示", message="密码不能为空")
        return
        
    # 调用 ChatSocket 发送登录请求
    if not client:
         messagebox.showerror("错误", "网络连接未初始化！")
         return
         
    login_result = client.login_type(user_name, password)

    if login_result == "1":
        print("登录成功！")
        go_to_main_panel(user_name) # 跳转到主界面
    elif login_result == "0":
        print("登录失败：用户名或密码错误。")
        messagebox.showerror(title="登录失败", message="用户名或密码错误！")
    elif login_result == "2": # (根据服务器端的协议添加)
        print("登录失败：该用户已在线。")
        messagebox.showerror(title="登录失败", message="该用户已在线！")
    else: # login_result is None 或其他意外情况
        print("登录失败：与服务器通信错误。")
        messagebox.showerror(title="登录失败", message="无法连接服务器或服务器响应异常。")

def handding_register():
    """处理登录界面的 '注册账号' 按钮点击"""
    print("切换到注册界面...")
    global register_frame
    
    if login_frame:
        login_frame.close_login_panel() # 关闭登录窗口

    # 创建 RegisterPanel 实例, 传入回调函数
    register_frame = RegisterPanel(file_open_face=file_open_face, 
                                     close_register_window=close_register_window, 
                                     register_submit=register_submit)
    register_frame.show_register_panel()
    # register_frame.load() # 注意：不要在这里调用 mainloop!

def close_register_window():
    """处理注册界面的 '返回' 按钮点击 (或 'X')"""
    print("从注册界面返回登录界面...")
    global login_frame
    
    if register_frame:
        register_frame.close_register_panel() # 关闭注册窗口

    # 重新创建并显示登录窗口
    login_frame = LoginPanel(handding_login, handding_register, close_login_window)
    login_frame.show_login_panel()
    # login_frame.load() # 不要在这里调用 mainloop!

def register_submit(register_panel_instance): # 参数是 RegisterPanel 实例
    """处理注册界面的 '立即注册' 按钮点击"""
    print("处理注册提交...")
    user_name, password, confirm_password, file_name = register_panel_instance.get_input()

    if not user_name or not password or not confirm_password:
        messagebox.showwarning("输入错误", "请填写所有必填项！")
        return
    if password != confirm_password:
        messagebox.showerror("输入错误", "两次输入的密码不一致！")
        return
    # if not file_name: # 检查是否选了头像，根据需要决定是否强制
    #     messagebox.showwarning("输入错误", "请选择头像！")
    #     return

    # 调用 ChatSocket 发送注册请求
    if not client:
         messagebox.showerror("错误", "网络连接未初始化！")
         return
         
    result = client.register_user(user_name, password, file_name)

    if result == "0":
        print("注册成功！")
        messagebox.showinfo("成功", "注册成功！现在您可以返回登录了。")
        close_register_window() # 注册成功后自动返回登录界面
    elif result == "1":
        print("注册失败：用户名已存在。")
        messagebox.showerror("注册失败", "该用户名已被注册！")
    elif result == "2":
        print("注册失败：发生未知数据库错误。")
        messagebox.showerror("注册失败", "服务器发生未知错误，请稍后再试。")
    else: # result is None 或其他意外
        print("注册失败：与服务器通信错误。")
        messagebox.showerror("注册失败", "无法连接服务器或服务器响应异常。")


# --- 聊天相关的回调 ---

def send_message(main_panel_instance, event=None): # 添加 event=None 兼容 bind('<Return>')
    """处理主界面的 '发送' 按钮点击 (或回车)"""
    global chat_user
    
    if not main_panel_instance or not client: return # 安全检查
    
    content = main_panel_instance.get_send_text()
    
    # 移除末尾可能由 Text 控件自动添加的换行符
    content = content.strip() 
    
    if not content:
        messagebox.showwarning(title="提示", message="不能发送空消息！")
        return
        
    print(f"发送消息 to '{chat_user}': {content}")
    
    # 清空输入框
    main_panel_instance.clear_send_text()
    
    # 调用 ChatSocket 发送消息
    sent = client.send_message(content, chat_user)
    if not sent:
        messagebox.showerror("发送失败", "发送消息时网络连接出现问题。")
        # (可能需要关闭窗口或尝试重连)

def send_mark(exp):
    """处理表情按钮点击后，由 MainPanel 的 mark 方法调用"""
    global chat_user
    
    if not client: return
    
    print(f"发送表情 to '{chat_user}': {exp}")
    
    # 表情也作为普通消息发送
    sent = client.send_message(exp, chat_user)
    if not sent:
        messagebox.showerror("发送失败", "发送表情时网络连接出现问题。")

def refurbish_user():
    """处理 '刷新在线用户' 按钮点击"""
    if not client: return
    
    print("请求刷新在线用户列表...")
    sent = client.send_refurbish_mark()
    if not sent:
         messagebox.showerror("请求失败", "发送刷新请求时网络连接出现问题。")

# --- 界面导航 ---

def go_to_main_panel(user_name):
    """登录成功后，关闭登录窗口，打开主聊天窗口"""
    global main_frame
    global is_running

    if login_frame:
        login_frame.close_login_panel() # 关闭登录窗口

    # 创建 MainPanel 实例
    main_frame = MainPanel(user_name=user_name, 
                           send_message=send_message, 
                           send_mark=send_mark, 
                           refurbish_user=refurbish_user, 
                           private_talk=private_talk, 
                           close_main_window=close_main_window)
                           
    # ！！！关键：启动接收线程！！！
    is_running = True
    recv_thread = threading.Thread(target=recv_data, daemon=True)
    recv_thread.start()
    print("消息接收线程已启动。")
    
    main_frame.show_main_panel() # 创建控件

    # ！！！关键：启动 GUI 消息检查循环！！！
    # 不要在 Panel 内部启动 mainloop, 由 Controller 控制
    # 我们用 after 来轮询 queue
    main_frame.main_frame.after(100, process_message_queue) 
    
    # 主线程继续执行（不需要 mainloop 了，因为 login 时已经启动）
    # 如果 login/register 是 Toplevel, 这里需要 main_frame.main_frame.mainloop()

# --- 消息接收与处理 (运行在子线程) ---

# !!! 警告：直接从子线程更新 Tkinter 控件是不安全的 !!!
# !!! 标准做法是使用 queue + after 将更新请求传递给主线程 !!!
# !!! 这里为了简化，暂时按参考代码的思路直接更新，但请注意风险 !!!
message_queue = None # 实际应该用 queue.Queue()

def recv_data():
    """
    运行在子线程中，负责持续接收服务器消息并处理。
    """
    global is_running
    
    if not client: return # 防御性编程

    while is_running:
        try:
            # 1. 接收标记
            marker = client.recv_all_string()
            if marker is None: # 连接断开
                if is_running: # 如果不是主动关闭
                     print("错误：与服务器的连接意外断开。")
                     # (可以尝试放入一个特殊标记到队列通知主线程)
                     # if message_queue: message_queue.put("SERVER_DISCONNECTED")
                break # 退出接收循环

            print(f"收到标记: {marker}")

            # 2. 根据标记处理
            if marker == "#!onlinelist#!":
                count = client.recv_number()
                if count is None: break
                users = []
                for _ in range(count):
                    user = client.recv_all_string()
                    if user is None: raise ConnectionError("接收用户列表时中断") # 出错则中断
                    users.append(user)
                
                # --- !!! 线程不安全 !!! ---
                if main_frame:
                    # 直接调用 GUI 更新 (不推荐)
                     # main_frame.refresh_friends(count, users) 
                     # 安全做法：放入队列
                     if message_queue: message_queue.put({'type': 'userlist', 'count': count, 'users': users})
                # --- !!! ---
                
            elif marker == "#!message#!":
                chat_flag = client.recv_all_string()
                if chat_flag is None: break
                sender = client.recv_all_string()
                if sender is None: break
                content = client.recv_all_string()
                if content is None: break

                # --- !!! 线程不安全 !!! ---
                if main_frame:
                    # 直接调用 GUI 更新 (不推荐)
                    # main_frame.show_send_message(sender, content, chat_flag)
                    # 安全做法：放入队列
                    if message_queue: message_queue.put({'type': 'message', 'flag': chat_flag, 'sender': sender, 'content': content})
                # --- !!! ---

            elif marker == "#!system#!": # (假设服务器会发这种标记)
                 system_message = client.recv_all_string()
                 if system_message is None: break
                 # --- !!! 线程不安全 !!! ---
                 if main_frame:
                     # 安全做法：放入队列
                     if message_queue: message_queue.put({'type': 'system', 'message': system_message})
                 # --- !!! ---
                 
            else:
                print(f"收到未知的服务器标记: {marker}")

        except ConnectionError as e: # 自定义错误或 recv 返回 None 后的处理
             if is_running: print(f"接收数据时连接错误: {e}")
             break # 退出循环
        except Exception as e:
            if is_running: print(f"接收数据时发生未知错误: {e}")
            # (可以选择 break 或 continue，取决于错误严重性)
            break # 发生未知错误通常也应该退出

    print("消息接收线程结束。")

# --- GUI 消息处理循环 (运行在主线程) ---

def process_message_queue():
    """
    运行在主线程，定时检查 message_queue 并更新 GUI。
    """
    global is_running
    
    if not message_queue: return # 如果队列没创建
    
    try:
        # 非阻塞地获取消息
        message = message_queue.get_nowait() 
        
        # 处理从接收线程放入的消息字典
        if isinstance(message, dict):
            msg_type = message.get('type')
            
            if msg_type == 'userlist':
                if main_frame:
                    main_frame.refresh_friends(message['count'], message['users'])
            elif msg_type == 'message':
                if main_frame:
                    main_frame.show_send_message(message['sender'], message['content'], message['flag'])
            elif msg_type == 'system':
                 if main_frame:
                     # (您需要决定如何显示系统消息, 比如在聊天框用特殊颜色)
                     main_frame.show_send_message("系统提示", message['message'], "system_flag") # 假设您添加了system_flag处理
                 else: # 如果主窗口还没创建就收到系统消息 (不太可能)
                     messagebox.showinfo("系统消息", message['message'])
                         
        # 处理特殊标记 (例如断开连接)
        elif message == 'SERVER_DISCONNECTED':
             is_running = False # 停止轮询
             if main_frame: main_frame.main_frame.after_cancel(process_message_queue) # 取消下一次调用
             messagebox.showerror("连接断开", "与服务器的连接已断开！")
             close_socket() # 关闭本地 socket
             if main_frame: main_frame.main_frame.destroy() # 关闭窗口
             # (可能需要返回登录界面)
             return # 不再安排下一次 after

    except queue.Empty:
        # 队列为空，什么都不做
        pass
    except Exception as e:
        print(f"处理消息队列时发生错误: {e}")

    # 只要还在运行，就安排下一次检查
    if is_running and main_frame and main_frame.main_frame:
        try:
             # 确保 main_frame 仍然存在 (窗口可能已被关闭)
             if main_frame.main_frame.winfo_exists():
                  main_frame.main_frame.after(100, process_message_queue)
        except tk.TclError:
             # 如果窗口在检查期间被销毁，会抛出 TclError
             is_running = False # 停止轮询

# --- 程序启动入口 ---

def go_to_login_panel():
    """初始化网络和登录界面"""
    global client
    global login_frame
    global message_queue # 初始化队列

    # 初始化队列
    import queue # 需要导入 queue
    message_queue = queue.Queue()

    # 创建 ChatSocket (会尝试连接)
    # (如果连接失败，ChatSocket 内部会 sys.exit)
    client = ChatSocket()

    # 创建 LoginPanel
    login_frame = LoginPanel(handding_login, handding_register, close_login_window)
    login_frame.show_login_panel()
    login_frame.load() # 启动登录窗口的 mainloop (程序阻塞于此)

# --- 主程序 ---
if __name__ == "__main__":
    go_to_login_panel()