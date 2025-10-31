import tkinter as tk
import time
class MainPanel:
    def __init__(self,user_name,send_message,send_mark,refurbish_user,private_talk,close_main_window):
        self.user_name=user_name
        self.send_message=send_message
        self.send_mark=send_mark
        self.refurbish_user=refurbish_user
        self.private_talk=private_talk
        self.close_main_window=close_main_window
        self.ee = 0
        self.face = []
        self.main_frame = None
        self.friend_list=None
        self.message_text=None
        self.send_text=None
        self.p1 = None # 表情图片1
        self.p2 = None # 表情图片2
        self.p3 = None # 表情按钮图片
        self.p4 = None # 聊天记录按钮图片
        self.dic = {}  # 表情字典也应该在加载图片后再填充
        self.label1=None
        self.b1=None
        self.b2=None
    def show_main_panel(self):
        self.main_frame = tk.Tk()
        self.main_frame.title("聊天室")
        # 设置背景颜色
        self.main_frame.configure(background="white")
        # 得到屏幕宽度，高度
        screen_width = self.main_frame.winfo_screenwidth()
        screen_height = self.main_frame.winfo_screenheight()
        # 声明宽度，高度变量
        width = 1000
        height = 800
        # 设置窗口在屏幕局中变量
        gm_str = "%dx%d+%d+%d" % (width, height, (screen_width - width) / 2,
        (screen_height - 1.2 * height) / 2)
        self.main_frame.geometry(gm_str)  # 设置窗口局中
        # 设置窗口不能改变大小
        self.main_frame.resizable(width=False, height=False)
        self.p1 = tk.PhotoImage(file='image_resource/开心.png') 
        self.p2 = tk.PhotoImage(file='image_resource/不开心.png')
        self.p3 = tk.PhotoImage(file='image_resource/表情按钮.png')
        self.p4 = tk.PhotoImage(file='image_resource/聊天记录按钮.png')
        # --- 填充字典 ---
        self.dic = {
            'aa**': self.p1, 
            'bb**': self.p2, 
        }

        # 顶部标题栏 (Label)：
        self.label1 = tk.Label(self.main_frame, text=f" 在线用户 python聊天室欢迎您：{self.user_name} ")
        self.label1.grid(row=0, column=0, columnspan=3, sticky="ew")
        # 这样您以后就可以通过 self.label1.config(text="...") 来改变它了
        # 创建一个 tk.Label（self.label1），显示欢迎信息和用户名。

        self.friend_list=tk.Listbox(self.main_frame)
        #######attention rowspan=3的意义尚不清楚
        self.friend_list.grid(row=1, column=0, rowspan=3,sticky="ns")
        self.friend_list.bind('<ButtonRelease-1>', self.private_talk)
        # 2. 创建“遥控器”
        sc_bar = tk.Scrollbar(self.main_frame)
        # 3. 把“遥控器”放在“电视”旁边
        sc_bar.grid(row=1, column=0, sticky="nse", rowspan=3) # rowspan=3 匹配 Listbox
        # 4. 关键绑定 1：告诉遥控器，它的命令要发给谁
        sc_bar.config(command=self.friend_list.yview)
        self.friend_list.config(yscrollcommand=sc_bar.set)
        self.message_text=tk.Text(self.main_frame,state="disabled")
        self.message_text.grid(row=1, column=1, sticky="nsew")
        msg_sc_bar= tk.Scrollbar(self.main_frame)
        msg_sc_bar.grid(row=1, column=1, sticky='nse', padx=(0, 1), pady=1)#放在文本框旁边,并相互绑定
        msg_sc_bar.config(command=self.message_text.yview)
        self.message_text.config(yscrollcommand=msg_sc_bar.set)

        ####attention为什么上面没有设置高度，这个却要设置高度5
        self.send_text=tk.Text(self.main_frame,height=5)
        self.send_text.grid(row=2, column=1, sticky="nsew")
        send_sc_bar= tk.Scrollbar(self.main_frame)
        send_sc_bar.grid(row=2, column=1, sticky='nse', padx=(0, 1), pady=1)#放在文本框旁边,并相互绑定
        send_sc_bar.config(command=self.send_text.yview)
        self.send_text.config(yscrollcommand=send_sc_bar.set)

        # --- 右下功能按钮 ---
        # (坐标参考了您最初贴出的示例代码，您可以根据需要调整)
        
        # “发送”按钮
        # 绑定到大脑的 send_message 回调, 用 lambda 传递 self
        send_button = tk.Button(self.main_frame, text="发送", 
                                bg="#00BFFF", fg="white", 
                                width=13, height=2, font=('黑体', 12),
                                command=lambda: self.send_message(self))
        send_button.place(x=650, y=640)

        # “关闭”按钮
        # 绑定到大脑的 close_main_window 回调
        close_button = tk.Button(self.main_frame, text="关闭", 
                                 bg="white", fg="black", 
                                 width=13, height=2, font=('黑体', 12),
                                 command=self.close_main_window)
        close_button.place(x=530, y=640)

        # “表情”按钮
        # 绑定到皮肤的 express 内部方法, 使用图片 p3
        # (确保 self.p3 在这之前已经被加载！)
        if self.p3: # 做个简单的检查，防止图片加载失败
            emoji_button = tk.Button(self.main_frame, image=self.p3, 
                                     relief=tk.FLAT, bd=0, 
                                     command=self.express)
            emoji_button.place(x=214, y=525)
        else:
            print("警告：表情按钮图片加载失败！")
            emoji_button_fallback = tk.Button(self.main_frame, text="表情",
                                              command=self.express)
            emoji_button_fallback.place(x=214, y=525)


        # “聊天记录”按钮
        # 绑定到皮肤的 create_window 内部方法, 使用图片 p4
        # (确保 self.p4 在这之前已经被加载！)
        if self.p4: # 做个简单的检查
             history_button = tk.Button(self.main_frame, image=self.p4, 
                                        relief=tk.FLAT, bd=0,
                                        command=self.create_window)
             history_button.place(x=250, y=525)
        else:
            print("警告：聊天记录按钮图片加载失败！")
            history_button_fallback = tk.Button(self.main_frame, text="记录",
                                                command=self.create_window)
            history_button_fallback.place(x=250, y=525)

        # “刷新在线用户”按钮
        # 绑定到大脑的 refurbish_user 回调
        refresh_button = tk.Button(self.main_frame, text="刷新在线用户", 
                                   bg="#00BFFF", fg="white", 
                                   width=13, height=2, font=('黑体', 12),
                                   command=self.refurbish_user)
        refresh_button.place(x=40, y=650) # 这个按钮在左下角，靠近用户列表

        # (可选) 绑定回车键到发送按钮
        # 当焦点在 send_text 输入框时，按回车等同于点击发送按钮
        # 注意：这里需要把 send_message 改成接收一个 event 参数(虽然不用)
        # self.send_text.bind('<Return>', lambda event: self.send_message(self)) 
        # 或者您可以在 send_message 定义时加一个默认参数 def send_message(self, event=None):
        self.main_frame.bind('<Return>', lambda event: self.send_message(self)) # 绑定整个窗口的回车键更简单点

        # --- 最后绑定窗口关闭协议 ---
        self.main_frame.protocol("WM_DELETE_WINDOW", self.close_main_window)

    def load(self):
        self.main_frame.mainloop()
    # 公共接口”（“大脑”指挥“皮肤”的工具）
    def get_send_text(self):
        return self.send_text.get('1.0', 'end-1c')
    def clear_send_text(self):
        self.send_text.delete('1.0', 'end')
    def refresh_friends(self, online_number, names):
        self.friend_list.delete(0, 'end')
        self.friend_list.insert(0, f'在线用户数: {online_number}')
        self.friend_list.insert(1, "【群聊】")
        for name in names:
            self.friend_list.insert('end', name)
    def show_send_message(self, user_name, content, chat_flag):
        self.message_text.config(state=tk.NORMAL)
        self.message_text.tag_config("tag_name", foreground="black")
        title = f"{user_name}{time.strftime('%H:%M:%S')}\n"
        self.message_text.insert(tk.END, title, "tag_name")
        if content in self.dic:
            self.message_text.image_create(tk.END, image=self.dic[content])
        else:
            self.message_text.insert(tk.END, content, "tag_name")
        self.message_text.insert(tk.END, "\n")
        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)
    def change_title(self, title):
        self.label1.config(text=title)    
    # --- 内部逻辑方法 (皮肤自己处理) ---

    def express(self):
        """处理“表情”按钮点击，弹出或隐藏表情选择"""
        if self.ee == 0:
            self.ee = 1
            # --- 创建表情按钮 ---
            # (确保 self.p1 和 self.p2 已经加载！)
            # (按钮位置需要您根据实际布局微调)
            if self.p1:
                # (注意：如果 __init__ 中没初始化 self.b1=None, 这里首次创建)
                self.b1 = tk.Button(self.main_frame, command=self.bb1, image=self.p1,
                                    relief=tk.FLAT, bd=0)
                self.b1.place(x=214, y=495) # 调整 y 坐标，放在输入框上方一点
            if self.p2:
                self.b2 = tk.Button(self.main_frame, command=self.bb2, image=self.p2,
                                    relief=tk.FLAT, bd=0)
                self.b2.place(x=254, y=495) # 放在 b1 旁边
            # (如果您未来增加更多表情按钮，在这里继续创建和 place)

        else: # 如果 ee == 1 (表情已打开)
            self.ee = 0
            # --- 销毁表情按钮 ---
            # (使用 hasattr 检查变量是否存在更安全)
            if hasattr(self, 'b1') and self.b1: 
                try:
                    self.b1.destroy()
                except tk.TclError: pass # 按钮可能已被销毁
            if hasattr(self, 'b2') and self.b2:
                try:
                    self.b2.destroy()
                except tk.TclError: pass
            # (如果未来增加更多表情按钮，在这里继续 destroy)

    def bb1(self):
        """处理第一个表情按钮点击"""
        self.mark('aa**') # 将代号 'aa**' 传递给 mark 方法

    def bb2(self):
        """处理第二个表情按钮点击"""
        self.mark('bb**') # 将代号 'bb**' 传递给 mark 方法

    # (如果您增加了 p3, p4... 就需要添加 bb3, bb4...)

    def mark(self, exp):
        """
        接收表情代号 exp，通知大脑，并关闭表情面板
        """
        # 1. 拨打“大脑”的电话，把表情代号传过去
        if self.send_mark: # 检查回调函数是否存在
            self.send_mark(exp)
        else:
            print("错误：send_mark 回调函数未设置！")

        # 2. 关闭表情面板 (通过再次调用 express 实现)
        self.express()
    # --- 以下方法已省略 ---
    def create_window(self):
        pass
    def show_chatting_records(self):
        pass
    def clear_chatting_records(self):
        pass
    def save_chatting_records(self, content):
        pass
