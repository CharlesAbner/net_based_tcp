import tkinter as tk
from PIL import Image , ImageTk
class RegisterPanel(object):
    def __init__(self,register_submit,file_open_face,close_register_window):
        self.close_register_window=close_register_window
        self.register_submit=register_submit
        self.file_open_face=file_open_face
        self.file_name=""

        self.face_show=None
        self.p=None
        self.p2=None

    def show_register_panel(self):
        self.register_frame = tk.Tk()
        self.register_frame.title("注册")
        self.user_name = tk.StringVar()
        self.password = tk.StringVar()
        self.confirm_password = tk.StringVar()
        # 设置背景颜色
        self.register_frame.configure(background="white")
        # 得到屏幕宽度，高度
        screen_width = self.register_frame.winfo_screenwidth()
        screen_height = self.register_frame.winfo_screenheight()
        # 声明宽度，高度变量
        width = 503
        height = 400
        # 设置窗口在屏幕局中变量
        gm_str = "%dx%d+%d+%d" % (width, height, (screen_width - width) / 2,
        (screen_height - 1.2 * height) / 2)
        self.register_frame.geometry(gm_str)  # 设置窗口局中
        self.register_frame.title("登录")   # 设置窗口标题
        # 设置窗口不能改变大小
        self.register_frame.resizable(width=False, height=False)

                # 创建"昵称"标签，并"粘"在(110, 230)的位置
        tk.Label(self.register_frame, text="昵称：").place(x=110, y=230)
        # 创建"密码"标签，并"粘"在(110, 260)的位置
        tk.Label(self.register_frame, text="密码：").place(x=110, y=260)
        tk.Label(self.register_frame, text="确认密码：").place(x=110, y=290)
        #         输入框” (Entry)：
  
        tk.Entry(self.register_frame, textvariable=self.user_name).place(x=180, y=230)
        # 创建三个 tk.StringVar() 变量（self.user_name, self.password, self.confirm_password）。

        tk.Entry(self.register_frame, textvariable=self.password,show="*").place(x=180, y=260)
        # 创建三个 tk.Entry 控件，分别用 textvariable= 属性绑定到这三个 StringVar 变量。

        tk.Entry(self.register_frame, textvariable=self.confirm_password,show="*").place(x=180, y=290)
        # （密码框和确认密码框要加 show='*'）。
        # 用 .place() 把它们粘在标签旁边。
        # “头像区” (Avatar Display)：
        # 这是示例代码里最复杂的地方，它用了一个 tk.Text 控件来显示图片。
        # 您的流程：
        # 创建一个 tk.Text 控件（self.face_show），设置它的大小，并用 .place() 放置。
        # 1. 创建 Text 控件，"地基"是 self.register_frame
        self.face_show = tk.Text(self.register_frame, width=7, height=3.5) 
        # 2. "粘"在窗口上
        self.face_show.place(x=370, y=230)
        # （高级技巧） 为了显示默认头像，您需要用 PIL 模块（Image.open("默认头像.png")）来加载、缩放（resize）图片。
        # 1. 用 PIL 打开图片
        pil_image_original = Image.open("image_resource\默认头像.png")
        # 2. 用 PIL 缩放图片。
        # (注意: Image.ANTIALIAS 已被弃用, 新版 PIL 推荐用 Image.Resampling.LANCZOS)
        pil_image_resized = pil_image_original.resize((50, 50), Image.Resampling.LANCZOS)
        # 把缩放后的图片转为 tk.PhotoImage 对象（self.p2）。
        # 1. 转换格式
        self.p2 = ImageTk.PhotoImage(pil_image_resized)
        # 4. 插入 (用 Tkinter)
        self.face_show.config(state=tk.NORMAL)           # 解锁
        self.face_show.image_create(tk.END, image=self.p2) # 插入
        self.face_show.config(state=tk.DISABLED)          # 锁定
        self.face_show.see(tk.END)
        #“按钮” (Button)：

        # “返回”按钮： command 绑定到 self.close_register_window（这是“大脑”给您的“电话号码”）。
        back_button=tk.Button(self.register_frame,text="返回",command=self.close_register_window)
        back_button.place(x=110, y=370)
        # “添加头像”按钮： command 绑定到 self.file_open_face（这是“大脑”给您的另一个“电话号码”）。
        add_image_button=tk.Button(self.register_frame,text="添加头像",command=self.file_open_face)
        add_image_button.place(x=110, y=350)
        # “立即注册”按钮： command 绑定到 lambda: self.register_submit(self)。（关键！ 再次使用 lambda 技巧，以便在“拨打电话”时，能把“皮肤”自己（self）作为参数传给“大脑”，让“大脑”可以反过来调用 self.get_input()）。
        register_button=tk.Button(self.register_frame,text="立刻注册",command=lambda: self.register_submit(self))
        register_button.place(x=110, y=330)
        # 用 .place() 把这三个按钮粘在正确的位置。
    def load(self):
        self.register_frame.mainloop()
    # --- 公共接口 (大脑会调用这些) ---
    def get_input(self):
        return self.user_name.get(), self.password.get(), self.confirm_password.get(), self.file_name
    def add_face(self, file_name):
        # 把传进来的 file_name 存到 self.file_name。
        self.file_name=file_name
        # 执行和show_register_panel里显示“默认头像”时一样的流程：
        # （高级技巧） 为了显示默认头像，您需要用 PIL 模块（Image.open("默认头像.png")）来加载、缩放（resize）图片。
        # 1. 用 PIL 打开图片
        pil_image_update = Image.open(file_name)
        # 2. 用 PIL 缩放图片。
        # (注意: Image.ANTIALIAS 已被弃用, 新版 PIL 推荐用 Image.Resampling.LANCZOS)
        pil_image_resized = pil_image_update.resize((50, 50), Image.Resampling.LANCZOS)
        # 把缩放后的图片转为 tk.PhotoImage 对象（self.p2）。
        # 1. 转换格式
        self.p = ImageTk.PhotoImage(pil_image_resized)
        # 4. 插入 (用 Tkinter)
        self.face_show.config(state=tk.NORMAL)           # 解锁
        self.face_show.delete('0.0', tk.END)
        self.face_show.image_create(tk.END, image=self.p) # 插入
        self.face_show.config(state=tk.DISABLED)          # 锁定
        self.face_show.see(tk.END)
    def close_register_panel(self):
        if self.register_frame: 
            self.register_frame.destroy()