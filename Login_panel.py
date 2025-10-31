import tkinter as tk
# 文件一：LoginPanel (登录界面) 的流程
# 它的职责： 提供一个“登录表单”，并把用户的“操作”通知给“大脑”。

class LoginPanel(object):
    def __init__(self,handle_login,handle_register,close_login_window):
        # “构造”过程 (__init__)：
        # 这个类在被“大脑”创建（new）时，必须从“大脑”那里接收几个“回调函数”（您可以想象成“大脑”的直线电话号码）。
        # 它需要接收至少三个“电话号码”：
        # handle_login：（当“登录”按钮被点击时，要拨打的电话）
        # handle_register：（当“注册”按钮被点击时，要拨打的电话）
        # close_login_window：（当用户点窗口“X”关闭时，要拨打的电话）
        # LoginPanel 不关心这些电话打通后“大脑”会干什么，它只负责把这几个号码存起来。
        self.handle_login = handle_login
        self.handle_register = handle_register
        self.close_login_window = close_login_window
        self.login_frame = None
        self.user_name_var = None
        self.password_var = None
    def show_login_panel(self):
        self.login_frame = tk.Tk()
        self.login_frame.title("登录")
        # 设置背景颜色
        self.login_frame.configure(background="white")
        # 得到屏幕宽度，高度
        screen_width = self.login_frame.winfo_screenwidth()
        screen_height = self.login_frame.winfo_screenheight()
        # 声明宽度，高度变量
        width = 503
        height = 400
        # 设置窗口在屏幕局中变量
        gm_str = "%dx%d+%d+%d" % (width, height, (screen_width - width) / 2,
        (screen_height - 1.2 * height) / 2)
        self.login_frame.geometry(gm_str)  # 设置窗口局中
        self.login_frame.title("登录")   # 设置窗口标题
        # 设置窗口不能改变大小
        self.login_frame.resizable(width=False, height=False)

        self.user_name_var=tk.StringVar()
        #现在地基好了，您要往上放“标签(Label)”、“输入框(Entry)”和“按钮(Button)”。
        tk.Entry(self.login_frame,textvariable=self.user_name_var).place(x=180,y=230)

        # "密码" 输入框 (绑定变量, 设为星号)
        self.password_var = tk.StringVar()
        tk.Entry(self.login_frame, textvariable=self.password_var, show='*').place(x=180, y=260)

        login_button=tk.Button(self.login_frame,text="登录",command=lambda: self.handle_login(self))
        register_button=tk.Button(self.login_frame,text="注册",command=self.handle_register)
        login_button.place(x=110, y=300)
        register_button.place(x=110, y=370)

        self.login_frame.protocol("WM_DELETE_WINDOW", self.close_login_window)
        # 创建"昵称"标签，并"粘"在(110, 230)的位置
        tk.Label(self.login_frame, text="昵称：").place(x=110, y=230)
        # 创建"密码"标签，并"粘"在(110, 260)的位置
        tk.Label(self.login_frame, text="密码：").place(x=110, y=260)
    def load(self):
        self.login_frame.mainloop()
    # --- 公共接口 (大脑会调用这些) ---
    def get_input(self):
        # 大脑通过这个函数拿走输入框的值
        return self.user_name_var.get(), self.password_var.get()
        
    def close_login_panel(self):
        # 大脑通过这个函数命令窗口销毁
        if self.login_frame:
            self.login_frame.destroy()



