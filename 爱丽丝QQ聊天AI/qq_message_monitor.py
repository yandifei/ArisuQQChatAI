"""这个库用来监控QQ消息，监控Q群成员的消息，以及监听QQ好友的消息
内置判断是Q群还是QQ好友
"""
# 系统自带的库
import os                           # 系统库
import re                           # 正则
import io                           # 输入输出流
import json                         # json格式解析
import shlex                        # 防止通配符解析被注入
import subprocess                   # 线程使用
from datetime import datetime       # 时间
from time import sleep              # 休眠
# 第三方库
import uiautomation                 # 核心库（ui界面操作）
import requests                     # 网络请求
import win32api                     # win32api操作
import win32gui                     # win32api操作
import win32con                     # win32api操作
import win32clipboard               # 剪切板操作
from PIL import Image               # 图片格式转换处理(pip install Pillow)

class QQMessageMonitor:
    def __init__(self,win_name="",monitor_name="",top_wait_time = 2):
        """
        参数:
        win_name: 左上角窗口名字(如果有备注名就填备注名)
        monitor_name: QQ号或发送者的名字
        top_wait_time : 默认2秒，设置置顶后等待qq渲染完成的属性，（如果电脑卡的话可以调大属性）
        """
        self.win_name = str(win_name)    # 左上角窗口名字(如果有备注名就填备注名) 强制转为字符串
        self.monitor_name = str(monitor_name)   # 强制转为字符串
        self.parameter_validation() # 调用函数对参数进行校验
        # 窗口初始化相关
        self.group_or_friend = None # 记录窗口QQ群还是好友
        self.qq_chat_win:uiautomation.WindowControl = self.find_qq_chat_win(self.top_window_traversal())   # 遍历顶层窗口->从顶层窗口中找到指定的qq聊天窗口
        self.hwnd = self.qq_chat_win.NativeWindowHandle # 被监听窗口的句柄
        self.show_win() # 如果窗口最小化就展示窗口
        self.cancel_top_win()   # 取消窗口置顶，防止窗口置顶失效
        self.top_win()  # 把窗口置顶，防止窗口被遮挡导致渲染停止无法监控窗口
        sleep(top_wait_time)   # 等待窗口完全置顶（qq置顶后渲染需要时间）
        self.pid = self.qq_chat_win.ProcessId   # 被监听窗口的进程ID
        self.geometry = self.qq_chat_win.BoundingRectangle  # 窗口的位置和大小
        self.x = self.geometry.left # 窗口x坐标
        self.y = self.geometry.top # 窗口y坐标
        self.weight = self.geometry.width() # 窗口长
        self.height = self.geometry.height() # 窗口宽
        print(f"成功绑定 \033[96m{win_name}\033[0m {self.jude_group_or_friend(self.qq_chat_win)}窗口并置顶窗口\t监听者：{monitor_name}")# 把对象进行绑定，动态属性修改并打印
        print(f"\033[96m{win_name}\033[0m 窗口句柄:{self.hwnd}\t进程ID:{self.pid}\t窗口大小:{self.geometry}")
        """------------------------------------------聊天窗口控制监控相关---------------------------------------------"""
        # 文档->组->组2(子孩子有2个组，第一个组是窗口控制按钮相关，第二个组是非窗口控制按钮的界面)
        self.main_chat_win = self.qq_chat_win.GetChildren()[0].GetChildren()[0].GetChildren()[1]
        # 文档->组->组2->组2(好友有2个组，群有3个组)可以用来区分qq还是群
        """标题栏(title_bar)[窗口控制按钮]"""
        self.top_button = self.main_chat_win.GetChildren()[0].GetChildren()[0]  #置顶（复合按钮）按钮
        self.min_button = self.main_chat_win.GetChildren()[0].GetChildren()[1]  # 最小化按钮
        self.max_button = self.main_chat_win.GetChildren()[0].GetChildren()[2]  # 最大化按钮
        self.close_button = self.main_chat_win.GetChildren()[0].GetChildren()[3]    # 关闭按钮
        """菜单栏(menu_bar)[菜单标题(好友名或群名和人数)、菜单选项按钮]"""
        # 2个组里面->组2->组1->组2->左上菜单栏->有2个组（1个是群名，一个是人数）
        self.menu_bar = self.main_chat_win.GetChildren()[1].GetChildren()[0].GetChildren()[1]    # 标题栏左边
        if self.group_or_friend == "群聊":
            self.menu_bar_button = self.menu_bar.GetChildren()[0] # 群按钮（群名或备注名和人数）
            self.menu_bar_group_name = self.menu_bar_button.GetChildren()[0] # 群名(群按钮子的第一个子孩子)
            self.menu_bar_group_count = self.menu_bar_button.GetChildren()[1] # 群人数(群按钮子的第二个子孩子)
        elif self.group_or_friend == "好友":
            self.menu_bar_button = self.menu_bar.GetChildren()[0]  # 好友按钮(好友名或备注名)
        # 2个组里面->组2->组1->组3->"更多"工具栏->6个组都菜单栏选项按钮（6个组里面对应语音通话、视频通话、屏幕共享、群应用、邀请加群、展开菜单的按钮）
        self.menu_option_buttons  =self.main_chat_win.GetChildren()[1].GetChildren()[0].GetChildren()[2].GetChildren()[0]
        self.voice_call_button = self.menu_option_buttons.GetChildren()[0].GetChildren()[0] # 语音通话
        self.video_call_button = self.menu_option_buttons.GetChildren()[1].GetChildren()[0] # 视频通话
        self.screen_share_toggle = self.menu_option_buttons.GetChildren()[2].GetChildren()[0] # 屏幕共享
        if self.group_or_friend == "群聊":
            self.group_application = self.menu_option_buttons.GetChildren()[3].GetChildren()[0] # 群应用
            self.invite_to_group_button = self.menu_option_buttons.GetChildren()[4].GetChildren()[0] # 邀请加群
        elif self.group_or_friend == "好友":
            self.remote_control = self.menu_option_buttons.GetChildren()[3].GetChildren()[0] # 远程协助
            self.group_building = self.menu_option_buttons.GetChildren()[4].GetChildren()[0]  # 发起群聊
        self.more_button = self.menu_option_buttons.GetChildren()[5].GetChildren()[0]  # 展开菜单的按钮
        """消息列表框(message_list_box)"""
        # 2个组里面->组2->组2->组1->组3->组0->组0->全是消息控件，需要解析
        self.message_list_box = self.main_chat_win.GetChildren()[1].GetChildren()[1].GetChildren()[0].GetChildren()[2].GetChildren()[0].GetChildren()[0]
        self.messages_count = 0  # 记录最大消息数(调用消息监控会更新)
        self.AutomationId_list = list()   # 记录获得消息控件的所有ID(调用消息监控会更新)
        self.message_list = list()  # 设置一个列表接收消息
        self.message_list_dict = list()  # 列表字典形式记录消息，用来完整记录消息体（和消息列表冲突了）
        self.get_messages() # 创建对象的时候就对窗口进行一次监听，并把记录保存下来(动态属性修改)
        self.control_id_index = 0  # 旧表的最后一个控件id下标，用来定位新表(默认新表的第一个控件遍历消息体)
        """编辑工具栏(edit_tool_bar)"""
        # 2个组里面->组2->组2->组2->组3->7个组(表情、截图、文件、图片、红包、语音、聊天记录)
        self.edit_tool_bar = self.main_chat_win.GetChildren()[1].GetChildren()[1].GetChildren()[1].GetChildren()[2]
        self.expression_button = self.edit_tool_bar.GetChildren()[0].GetChildren()[0]   # 表情按钮
        self.screenshot_button = self.edit_tool_bar.GetChildren()[1].GetChildren()[0]   # 截图按钮
        self.screenshot_arrow = self.edit_tool_bar.GetChildren()[1].GetChildren()[1].GetChildren()[0] # 截图 Alt + S弹出菜单
        self.folder_button = self.edit_tool_bar.GetChildren()[2].GetChildren()[0]   # 文件按钮
        self.folder_arrow_button2 = self.edit_tool_bar.GetChildren()[2].GetChildren()[1].GetChildren()[0]  # 文件弹出菜单
        self.image_button = self.edit_tool_bar.GetChildren()[3].GetChildren()[0]   # 图片按钮
        if self.group_or_friend == "群聊":
            self.lucky_money_button = self.edit_tool_bar.GetChildren()[4].GetChildren()[0]   # 红包按钮
            self.microphone_on_button = self.edit_tool_bar.GetChildren()[5].GetChildren()[0]   # 语音按钮
        elif self.group_or_friend == "好友":
            self.shake_button = self.edit_tool_bar.GetChildren()[4].GetChildren()[0]   # 窗口抖动按钮
            self.lucky_money_button = self.edit_tool_bar.GetChildren()[5].GetChildren()[0]   # 红包按钮
            self.microphone_on_button = self.edit_tool_bar.GetChildren()[6].GetChildren()[0]   # 语音按钮
        if self.edit_tool_bar.GetChildren()[6].GetChildren()[0] == "机器人指令":  # qq群和好友不会起冲突(qq群这里可能少一个按钮)
            self.message_record_button = self.edit_tool_bar.GetChildren()[7].GetChildren()[0]   # 聊天记录按钮
        elif self.edit_tool_bar.GetChildren()[6].GetChildren()[0] == "聊天记录":    # 少了机器人指令按钮
            self.message_record_button = self.edit_tool_bar.GetChildren()[6].GetChildren()[0]  # 聊天记录按钮
        """编辑框(edit_box)[textbox、关闭按钮、发送按钮]"""
        # 2个组里面->组2->组2->组2->组4->组->组1("编辑"EditControl)[这个下面还有一个TextControl"文本"的子控件]
        self.edit_box: uiautomation.EditControl = self.main_chat_win.GetChildren()[1].GetChildren()[1].GetChildren()[1].GetChildren()[3].GetChildren()[0].GetChildren()[1]
        # 2个组里面->组2->组2->组2->组4->组->组1->组(TextControl"文本")
        self.text_control: uiautomation.TextControl = self.main_chat_win.GetChildren()[1].GetChildren()[1].GetChildren()[1].GetChildren()[3].GetFirstChildControl().GetChildren()[1].GetFirstChildControl()
        # 2个组里面->组2->组2->组2->组5->组1(关闭按钮)
        self.edit_box_close_button =  self.main_chat_win.GetChildren()[1].GetChildren()[1].GetChildren()[1].GetChildren()[4].GetChildren()[0]
        # 2个组里面->组2->组2->组2->组5->组2->组1(发送按钮)
        self.send_button = self.main_chat_win.GetChildren()[1].GetChildren()[1].GetChildren()[1].GetChildren()[4].GetChildren()[1].GetChildren()[0]
        """文件发送时的按钮"""
        # 文档->组->倒数第二个组(对话框)->最后组->最后组->组(发送(1)的按钮)

        """公告栏(bulletin_bar)[群公告文本控件、群公告按钮、可见的群公告文本]"""
        if self.group_or_friend == "群聊" and len(self.main_chat_win.GetChildren()[1].GetChildren()[2].GetChildren()[0].GetChildren()) == 5:  # 如果等于4就代表没有公告，5才有公告
            # 2个组里面->组3->组1->组1->组1(有3个子孩子[群公告文本、群公告按钮、可见的群公告文本])
            self.bulletin_bar = self.main_chat_win.GetChildren()[1].GetChildren()[2].GetChildren()[0].GetChildren()[0]
            # self.bulletin_text_button = self.bulletin_bar.GetChildren()[0].GetChildren()[0] # 群公告文字（节约空间）
            self.group_bulletin_button = self.bulletin_bar.GetChildren()[1] # 群公告按钮
            if len(self.bulletin_bar.GetChildren()[2].GetChildren()) == 0:    # 如果自己是群主或管理员没设置公告就会有这个
                self.visible_group_bulletin = None  # 群公告为空
            else:   # 调用群公告解析
                self.visible_group_bulletin = self.bulletin_split(self.bulletin_bar.GetChildren()[2]) # 可见的群公告
        """群成员框(group_member_box)[文本控件(群聊成员人数)、群成员搜索、群成员列表]"""
        if self.group_or_friend == "群聊":
            group_or_friend_index = 1   # 群成员位置下表
            if len(self.main_chat_win.GetChildren()[1].GetChildren()[2].GetChildren()[0].GetChildren()) == 4:   # 没有公告栏存在控件位置影响
                group_or_friend_index = 0   # 如果没有控件就是从0开始的下标
            # 2个组里面->组3->组1->组1->组2(直接文本控件(群聊成员人数))
            self.group_member_count = self.main_chat_win.GetChildren()[1].GetChildren()[2].GetChildren()[0].GetChildren()[group_or_friend_index]    # 群聊成员人数
            # 2个组里面->组3->组1->组1->组3(群搜索按钮)
            self.group_member_search = self.main_chat_win.GetChildren()[1].GetChildren()[2].GetChildren()[0].GetChildren()[group_or_friend_index + 1]
            # 2个组里面->组3->组1->组1->组4->组->组2(群成员搜索输入框("编辑"EditControl))
            self.group_member_search_input_box= self.main_chat_win.GetChildren()[1].GetChildren()[2].GetChildren()[0].GetChildren()[group_or_friend_index + 2].GetChildren()[0].GetChildren()[1]    # 群聊成员人数
            # 2个组里面->组3->组1->组1->组5->"成员列表"(一堆子组(记录群员和职称，如果是群友就没有称呼))
            self.group_member_list = self.main_chat_win.GetChildren()[1].GetChildren()[2].GetChildren()[0].GetChildren()[group_or_friend_index + 3].GetChildren()[0]
            # QQ群主和管理员
            self.qq_group_administrator = self.get_qq_group_administrator()
        """-----------------------------------------消息监听相关-----------------------------------------"""
        self.message_data_directory = None   # 监听数据存放的目录
        self.message_data_txt = None    # 监听的文本数据存放路径
        self.create_directory()  # 如果没有转义这里会报警告，不用管(创建目录)
        self.create_txt()  # 创建文本文件
        self.message_processing_queues = list() # 消息处理队列(接收到指定消息后就把消息进行处理)
        self.keyword_respond = False    # 是否启动关键词自动回复
        self.message_keyword = list()   # 消息关键词
        self.sender_keyword = list()   # 发送者关键词.txt
        self.message_sender_keyword = dict()    # 指定发送者的关键词
        self.filter_sender_keyword = list()     # 过滤发送者关键词.txt
        self.keyword_read() # 关键词读取(发送者及其关键词内容读入)
        """输出重定向的文本（显示文本）"""
        self.output_text = (f"成功绑定 {win_name} {self.jude_group_or_friend(self.qq_chat_win)}窗口并置顶窗口\t监听者：{monitor_name}\n"
                            f"{win_name} 窗口句柄:{self.hwnd}\t进程ID:{self.pid}\n窗口大小:{self.geometry}")

    def parameter_validation(self):
        """创建对象时对输入的信息进行校验"""
        if self.win_name == "":
            raise ValueError("请填写聊天框的名字")
        elif self.win_name == "QQ":
            raise ValueError("检测到需要监听的窗口名是QQ，请改备注名")
        if self.monitor_name == "":
            raise ValueError("请填写你的身份(群中的称号或QQ号或QQ名)")

    """顶层窗口遍历查找相关"""
    @staticmethod
    def refind(obj):
        """刷新控件，1.控件发生变化就需要刷新 2.建立新的窗口时也要刷新
        参数：obj：传入刷新对象
        """
        obj.Refind()  # 刷新控件

    @staticmethod
    def top_window_traversal(out=False):   # 顶层窗口遍历
        """获得当前的根窗口的所有可见窗口
        参数：out   ： 默认false不打印
        返回值： visible_windows_object（list）     ：   桌面可见的列表
        """
        desktop = uiautomation.GetRootControl()  # 获取当前桌面对象
        if out: print(f"{desktop.Name}的可见窗口为:")
        visible_windows = desktop.GetChildren()  # 获得当前桌面所有可见的窗口的对象
        visible_windows_object = list()     # 列表存放可见窗口的对象
        for visible_window in visible_windows:
            visible_windows_object.append(visible_window)   #   遍历存放可见窗口的对象
        if out:
            for window in visible_windows_object: print(window.Name)# 打印找到的窗口名
        return visible_windows_object

    def find_qq_chat_win(self,visible_windows_object):
        """遍历顶层窗口找到指定qq聊天窗口
        :参数 visible_windows_object: 可见窗口的列表
        :返回值:指定窗口的对象
        """
        qq_chat_win_list = list() # 如果标题和类名相同就拒绝绑定
        for visible_window in visible_windows_object:
            # 找到符合指定好友名或qq群名的窗口
            if visible_window.Name == self.win_name and visible_window.ClassName == "Chrome_WidgetWin_1":
                qq_chat_win_list.append(visible_window) # 把查找对象添加进去
        if len(qq_chat_win_list) == 0:
            raise ValueError(f"没有找到这个窗口\n\n错误提示：\n请手动打开【{self.win_name}】 Q群将该Q群窗口显示到桌面上，你不开Q群我玩个屁！我不是神不知道你想的啥！")
        elif len(qq_chat_win_list) >= 2:
            raise ValueError("窗口重名\n\n错误提示：\n请确保当前打开的Q群没有重名(有备注名就看备注名，没有就是原来的Q的名)。")
        return qq_chat_win_list[0]

    """窗口判定相关"""
    @staticmethod
    def is_qq(obj):
        """检测是不是qq窗口的结构
        参数：obj ：需要判断的对象
        返回值：False 或 True
        """
        try:
            if len(obj.GetChildren()[0].GetChildren()[0].GetChildren()[0].GetChildren()) == 4:
                return True
        except():
            raise ValueError("请把qq窗口置顶并展示在在桌面上")
        return False

    def jude_group_or_friend(self,obj):
        """判断该对话框是QQ群还是qq好友(根据结构判断)
        参数：obj：窗口的对象
        返回值： "群聊" 或 "好友"
        会该变self.group_or_friend属性
        """
        # 检查结构（不需要担心是QQ窗口，考虑qq群还是qq好友就行）
        obj.Refind()    # 刷新控件
        self.qq_chat_win = self.find_qq_chat_win(self.top_window_traversal())  # 重新强制刷新窗口
        # 尝试了这么多方法还是这个实在,确保窗口控件能被成功读取
        self.top_win()  # 重新置顶窗口
        try:    # 如果群有机器人就会溢出
            if obj.GetChildren()[0].LocalizedControlType != "文档":
                # sleep(1)
                print(obj.GetChildren()[0].LocalizedControlType)
                print(obj.GetChildren()[1].LocalizedControlType)
                raise EnvironmentError(f"请把“{self.win_name}”窗口置顶显示在桌面上或重新启动程序")
            # 文档->组->第二个组->第二个组->群聊3个|好友2个组
            elif len(obj.GetChildren()[0].GetChildren()[0].GetChildren()[1].GetChildren()[1].GetChildren()) == 3:
                self.group_or_friend = "群聊"
                return "群聊"
            elif len(obj.GetChildren()[0].GetChildren()[0].GetChildren()[1].GetChildren()[1].GetChildren()) == 2:
                self.group_or_friend = "好友"
                return "好友"
        except IndexError:
            return "群聊"
        return False    # 窗口没有显示在桌面上

    """窗口控制和控件操作相关"""
    def move(self,x = None, y = None,repaint=True):
        """qq聊天窗口位置移动(如果什么都不填就把窗口移动到最左上角只留一个像素，不要多次调用)
        x ： 窗口左上角的x坐标
        y ： 窗口左上角的y坐标
        repaint : 重新绘制窗口，默认打开
        """
        if x == y is None:  # 把窗口移动到指定位置
            x = 3 - self.weight
            y = 3 - self.height
        size = win32gui.GetWindowRect(self.hwnd)  # 获取窗口左上角和右下角的坐标
        width, height = size[2] - size[0], size[3] - size[1]    # 计算窗口的大小
        win32gui.MoveWindow(self.hwnd, x, y, width, height, repaint)

    def show_win(self):
        """展示qq窗口，如果qq窗口最小化就展示出来"""
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)

    def set_size(self, width, height, repaint=True):
        """改变qq聊天窗口的大小（坐标保持在左上角）
        width ： 设置窗口的宽度
        height ： 设置窗口的高度
        repaint : 重新绘制窗口，默认打开
        """
        point = win32gui.GetWindowRect(self.hwnd)  # 获取窗口左上角和右下角的坐标
        win32gui.MoveWindow(self.hwnd, point[0], point[1], width, height, repaint)

    def keep_size(self, repaint=True):
        """保持窗口最开始属性的大小
        repaint : 重新绘制窗口，默认打开
        """
        point = win32gui.GetWindowRect(self.hwnd)  # 获取窗口左上角和右下角的坐标
        win32gui.MoveWindow(self.hwnd, point[0], point[1], self.weight, self.height, repaint)

    def top_win(self):
        """将qq聊天窗口置顶"""
        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_TOPMOST,  # 置顶层
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )

    def cancel_top_win(self):
        """取消窗口置顶
        hwnd ： 窗口的句柄
        """
        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_NOTOPMOST,  # 取消置顶
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )

    @staticmethod
    def get_hwnd(control):
        """获得控件的窗口句柄
        参数：control：控件对象
        返回值：控件的句柄
        """
        return control.NativeWindowHandle

    @staticmethod
    def get_position(control):
        """获得控件的中心位置
        参数：control：控件对象
        返回值：控件的中心坐标
        """
        return control.BoundingRectangle.xcenter(),control.BoundingRectangle.ycenter()

    @staticmethod
    def click(control):
        """鼠标瞬移到控件中心点击
        参数：control：控件对象
        """
        uiautomation.Click(control.BoundingRectangle.xcenter(), control.BoundingRectangle.ycenter())

    def send_click(self,control):
        """向窗口发送点击消息
        参数：control：控件对象
        """
        # 获取控件中心x和y的绝对坐标
        screen_x, screen_y = control.BoundingRectangle.xcenter(),control.BoundingRectangle.ycenter()
        # 把屏幕坐标转换为客户端坐标（应用窗口的坐标）
        client_x, client_y = win32gui.ScreenToClient(self.hwnd, (screen_x, screen_y))
        # 模拟鼠标指针， 传送到指定坐标（坐标必须是相对坐标即客户端坐标）
        long_position = win32api.MAKELONG(client_x, client_y)
        # 模拟鼠标按下(窗口句柄和客户端坐标)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_position)
        # 模拟鼠标弹起(窗口句柄和客户端坐标)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, long_position)

    @staticmethod
    def key(control,content):
        """向控件逐个输入字符(光标一直在第一个位置)
        参数：control：控件对象
        content : 发送的内容
        """
        # content =  # 反转倒序content[::-1]
        # print(content)
        control.SendKeys(content)

    @staticmethod
    def set_value(control,value):
        """设置编辑控件得值(qq编辑控件不起作用不知道是为什么)
        参数：control：控件对象
        value : 需要设置的值
        """
        print(control.GetValuePattern().Value)
        control.GetValuePattern().SetValue(value)

    @staticmethod
    def send_key(control,content):
        """向窗口发送按键消息
        参数：control：控件对象
        content : 发送文本
        """
        # self.edit_box.GetValuePattern().SetValue('sfsfsdfsfsdf')
        # self.send_click(control)    # 必须先后台点击一下窗口激活，不然就会导致输出乱来
        # content[::-1]
        for char in content:
            control.edit_box.SendKeys(char)
        #

    """消息写入相关(复制文本或图片，粘贴到编辑控件)"""
    @staticmethod
    def get_copy(out=False):
        """获得剪切板的内容
        参数 ： out: 默认False不输出提示
        返回值：返回剪切的内容
        """
        data = None # 放置剪切板内容
        # 获取剪切板内容
        try:
            # 打开剪切板
            win32clipboard.OpenClipboard()
            # 尝试获取 Unicode 文本（最常用格式）
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            # 获取位图
            elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            # 获取文件列表
            elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                files = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                if out: print(f"复制的文件: {files}")
            # 尝试获取 ANSI 文本
            elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                # 如果是字节字符串则解码为文本
                if isinstance(data, bytes):
                    data = data.decode("latin1")  # 或使用当前系统编码
            else:
                if out: print("剪切板内容为空")
            if out: print("剪切板内容:", data)
            return data
        finally:
            # 确保关闭剪切板
            win32clipboard.CloseClipboard()

    @staticmethod
    def set_copy(content):
        """把文本消息复制到剪切版(设置剪切板内容)
        参数 ： content 设置剪切板的内容
        """
        uiautomation.SetClipboardText(content)

    def copy_file(self, file_path):
        """复制文件到剪切板
        file_path : 文件路径
        """
        # 构建复制指令
        safe_path = shlex.quote(file_path)  # 安全转义路径 + 使用 LiteralPath 防止通配符解析
        copy_order = ['powershell', rf"Get-Item {safe_path} | Set-Clipboard"]
        try:
            # 执行指令，并捕获所有信息
            # check=True: 如果返回码非0，会自动抛出 CalledProcessError 异常
            # capture_output=True: 捕获 stdout 和 stderr
            # text=True: 将 stdout 和 stderr 解码为文本
            subprocess.run(
                args=copy_order,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'  # 显式指定编码
            )
            return True
        except FileNotFoundError:
            # print("'powershell' 命令未找到。请确保 PowerShell 已安装并且在系统的 PATH 环境变量中。")
            self.output_text = "'powershell' 命令未找到。请确保 PowerShell 已安装并且在系统的 PATH 环境变量中。"
        except subprocess.CalledProcessError as e:
            # 如果 check=True 并且返回码非0，则会进入这里
            # print(f"返回码: {e.returncode}")
            self.output_text = f"返回码: {e.returncode}"
        except Exception as e:
            # print(f"发生了未知错误: {e}")
            self.output_text = f"发生了未知错误: {e}"
        return False

    def edit_paste(self):
        """把剪切板的内容粘贴到文本编辑控件"""
        self.edit_box.SendKeys("{ctrl}v")

    def edit_send_key(self,content):
        """向QQ的消息编辑控件发送文本内容
        参数 ： content 输入的内容
        """
        self.edit_box.SetFocus()           # 设置焦点
        sleep(1)
        self.edit_box.SendKeys(content)    # 发送内容

    def send_message(self,data):
        """通过复制粘贴数据到qq发送控件
        参数：data ： 发送的数据
        """
        """对窗口进行激活操作"""
        # 先发送 WM_ACTIVATE 激活窗口再发送 WA_CLICKACTIVE 鼠标激活
        # win32api.SendMessage(self.hwnd, win32con.WM_ACTIVATE, win32con.WA_CLICKACTIVE, 0)
        # sleep(1)  # 发送前确保窗口激活
        # win32gui.SetForegroundWindow(self.hwnd)
        # sleep(0.1)  # 给窗口激活留出时间
        self.edit_box.SetFocus()    # 设置焦点
        """将文本复制到剪贴板"""
        win32clipboard.OpenClipboard()   # 打开剪切板
        win32clipboard.EmptyClipboard()  # 清空剪贴板
        # 设置Unicode文本
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, data)
        win32clipboard.CloseClipboard() # 关闭剪切板
        """模拟Ctrl+V按键"""
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)  # 按下Ctrl
        win32api.keybd_event(ord('V'), 0, 0, 0)             # 按下V
        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放V
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放Ctrl
        # 给窗口粘贴完毕的时间
        # while self.edit_box.GetFirstChildControl().GetFirstChildControl().Name == "":
        sleep(0.1)
        """后台点击发送按钮"""
        # 获取发送按钮中心x和y的绝对坐标
        screen_x, screen_y = self.send_button.BoundingRectangle.xcenter(), self.send_button.BoundingRectangle.ycenter()
        # 把屏幕坐标转换为客户端坐标（应用窗口的坐标）
        client_x, client_y = win32gui.ScreenToClient(self.hwnd, (screen_x, screen_y))
        # 坐标转换，16位的整数（通常是坐标值）合并成一个32位的长整型值
        long_position = win32api.MAKELONG(client_x, client_y)
        # 模拟鼠标指针， 传送到指定坐标（坐标必须是相对坐标即客户端坐标）
        win32api.SendMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, long_position)
        # 不给窗口粘贴完毕的时间
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_position)
        # 模拟鼠标弹起(窗口句柄和客户端坐标)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, long_position)

    def ctrl_v(self):
        """模拟ctrl+v的操作"""
        # win32gui.SetForegroundWindow(self.hwnd)
        self.edit_box.SetFocus()    # 设置焦点
        """模拟Ctrl+V按键"""
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)  # 按下Ctrl
        win32api.keybd_event(ord('V'), 0, 0, 0)  # 按下V
        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放V
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放Ctrl
        # 给窗口粘贴完毕的时间
        # while self.edit_box.GetFirstChildControl().GetFirstChildControl().Name == "":
        sleep(1)
        """后台点击发送按钮"""
        # 获取发送按钮中心x和y的绝对坐标
        screen_x, screen_y = self.send_button.BoundingRectangle.xcenter(), self.send_button.BoundingRectangle.ycenter()
        # 把屏幕坐标转换为客户端坐标（应用窗口的坐标）
        client_x, client_y = win32gui.ScreenToClient(self.hwnd, (screen_x, screen_y))
        # 坐标转换，16位的整数（通常是坐标值）合并成一个32位的长整型值
        long_position = win32api.MAKELONG(client_x, client_y)
        # 鼠标模拟移动过去
        win32api.SendMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, long_position)
        # 模拟鼠标双击(窗口句柄和客户端坐标)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, long_position)
        # 模拟鼠标弹起
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, long_position)  # 弹起

    def paste_send_file(self):
        """模拟粘贴发送文件"""
        self.edit_box.SetFocus()    # 设置焦点
        """模拟Ctrl+V按键"""
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)  # 按下Ctrl
        win32api.keybd_event(ord('V'), 0, 0, 0)  # 按下V
        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放V
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放
        sleep(1)    # 等待发送窗口显示
        """后台点击发送按钮"""
        # 拿到新弹出窗口的发送按钮
        # q群窗口->文档->组->倒数第二个组(对话框)->最后组->最后组->组(发送(1)的按钮)
        send_file_button = self.qq_chat_win.GetFirstChildControl().GetFirstChildControl().GetChildren()[-2].GetLastChildControl().GetLastChildControl().GetFirstChildControl()
        # 获取发送按钮中心x和y的绝对坐标
        screen_x, screen_y = send_file_button.BoundingRectangle.xcenter(), send_file_button.BoundingRectangle.ycenter()
        # 把屏幕坐标转换为客户端坐标（应用窗口的坐标）
        client_x, client_y = win32gui.ScreenToClient(self.hwnd, (screen_x, screen_y))
        # 坐标转换，16位的整数（通常是坐标值）合并成一个32位的长整型值
        long_position = win32api.MAKELONG(client_x, client_y)
        # 鼠标模拟移动过去
        win32api.SendMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, long_position)
        # 模拟鼠标双击(窗口句柄和客户端坐标)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, long_position)
        # 模拟鼠标弹起
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, long_position)  # 弹起


    def get_edit_value(self):
        """获取编辑控件的值
        返回值： 文本编辑框的内容
        """
        return self.edit_box.GetValuePattern().Value

    def set_edit_value(self,content):
        """修改edit控件的值
        参数 ： content ： 需要修改的文本内容
        """
        self.edit_box.SetFocus()   # 设置焦点
        self.edit_box.GetValuePattern().SetValue("content")
        pass

    # def set_edit_title(self):
    #     """获取窗口标题并修改窗口标题"""
    #     print(self.edit_box.Name)
    #     self.edit_box.SetWindowText("1234")

    """额外模块"""
    @staticmethod
    def copy_pic(image_path):
        """复制图片(把图片放到剪切板)"""
        # 读取图片并转换为RGB模式
        image = Image.open(image_path).convert("RGB")
        # 将图片保存为BMP格式的内存字节流
        output = io.BytesIO()
        image.save(output, format="BMP")
        bmp_data = output.getvalue()
        output.close()
        # 去除BMP文件头（14字节），获取DIB数据
        dib_data = bmp_data[14:]
        # 将DIB数据写入剪贴板
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib_data)
        win32clipboard.CloseClipboard()

    def send_url_image(self, url):
        """使用接口发送图片
        url : 图片接口
        https://t.alcy.cc/moe   # 二次元萌图
        https://v2.xxapi.cn/api/baisi?return=302   # 三次元白丝
        https://v2.xxapi.cn/api/heisi?return=302   # 三次元黑丝
        """
        try:
            # 请求超过10秒为超时
            with Image.open(io.BytesIO(requests.get(url, timeout=10).content)) as img:
                img.save("./logs/下载缓存/网页请求图片.png", "PNG")
            # 设置剪切板内容为图片
            self.copy_pic("./logs/下载缓存/网页请求图片.png") # 处理图片并复制到剪切板
            self.ctrl_v()   # 模拟粘贴操作并发送
        except Exception as e:
            # print(f"\033[91m图片无法发送(9成网络问题)，出现异常错误:{e}")  # 设置剪切板内容出现异常
            self.output_text = f"图片无法发送(9成网络问题)，出现异常错误:{e}"

    """消息窗口监听相关"""
    @staticmethod
    def bulletin_split(obj):
        """公告文本解析（2层）可以判断该是否有公告消息，但是必须存在公告这个控件（群主可以不写公告但会有这个框）
        参数:obj:公告对象
        """
        # 无、1层、2层（链接）
        bulletin_message = ""   # 信息存储
        if len(obj.GetChildren()) != 0:
            for i in obj.GetChildren():
                if len(i.GetChildren()) != 0:   # 存在子控件需要深度查找
                    for j in i.GetChildren():
                        if j.LocalizedControlType == "文本":
                            bulletin_message += j.Name + " " # 添加文本
                elif i.LocalizedControlType == "文本":    # 没有子控件
                    bulletin_message += i.Name + " " # 添加文本
        return bulletin_message

    def get_qq_group_administrator(self):
        """解析Q群的管理员和群主(方法这么命名是因为群主最大同时也有管理员的权限)
        返回值： qq_group_administrator_list ： QQ管理员列表(第一个元素为群主)
        """
        # [administrator for administrator in self.group_member_list if self.group_member_list.GetChildren()[2].GetChildren()[0].Name == "管理员"]
        qq_group_administrator_list = list()    # 群成员列表
        # 判断好友列表第一个人是否为群主
        if len(self.group_member_list.GetChildren()[0].GetChildren())  != 3:
            raise ValueError("请将群成员列表滚到最开头(有群主的标志)")
        # 收录群主的名字
        qq_group_administrator_list.append(self.group_member_list.GetChildren()[0].GetChildren()[1].Name)
        for administrator in self.group_member_list.GetChildren()[1:]:    # 遍历成员列表(跳过群组遍历)
            if len(administrator.GetChildren()) == 3:    # 检测身份(不是管理员或群主没有3个控件，这个控件记录身份)
                qq_group_administrator_list.append(administrator.GetChildren()[1].Name)     # 添加管理员身份
        return qq_group_administrator_list

    def create_directory(self,path=None,use=False,out=False):
        """创建监听者和监听窗口的目录
        参数：path：默认为None(库的上级目录下创建)，如果填入就在填入路径下创建
        use: 默认为false如果指定目录存在要创建的文件夹就爆错
        out : 是否打印输出提示,默认False
        """
        monitor_directory = re.sub(r'[\\/:*?"<>|]', '_', self.monitor_name) # 剔除监听者无效字符
        messages_data_directory = re.sub(r'[\\/:*?"<>|]', '_', self.win_name) # 剔除监听窗口无效字符
        if path is None:    # 如果路径不填就在本级logs目录下创建一个文件夹
            try:
                self.message_data_directory = os.path.join("./logs",monitor_directory,messages_data_directory)   # 路径拼接
                os.makedirs(self.message_data_directory)
                if out: print(f"成功创建监听者目录:{monitor_directory}\t{self.group_or_friend}“{self.win_name}”消息将存放到该目录中")
                self.output_text = f"成功创建监听者目录:{monitor_directory}\t{self.group_or_friend}“{self.win_name}”消息将存放到该目录中"
            except FileExistsError: # 路径一定存在且合法
                if out: print(f"已存在监听者目录:{monitor_directory}\t{self.group_or_friend}“{self.win_name}”的监听消息将继续存放到该目录中")
        else:
            try:
                path = rf"{path}" # 对输入的路径进行转义
                self.message_data_directory = os.path.join(path, monitor_directory,messages_data_directory) # 拼接多级目录
                os.makedirs(self.message_data_directory)  # 创建多级目录
                if out: print(f"成功创建监听者目录:{monitor_directory}\t{self.group_or_friend}“{self.win_name}”消息将存放到该目录中")
            except FileExistsError:
                if not use: # 如果未开启沿用就报错(防止不小心对重要文件进行操作)
                    raise EnvironmentError(f"文件夹已存在“{monitor_directory}”目录，请转移该目录或删除该目录，如果要沿用该目录请填入参数")
            except OSError:
                raise ValueError("输入的路径不存在，创建目录失败")

    def create_txt(self,path=None):
        """在指定目录下创建一个txt文本文件存放置聊天记录
        如果该文件存在就直接覆写，不会进行追加(因为创建目录的时候就必须填入沿用的参数就代表了知道会修改的问题)
        """
        if path is None:    # 默认写入到建立好的文件夹(这里不用对self.message_data_directory路径进行检查因为获取时已经检查过了)
            if self.message_data_directory is None: # 如果直接调用这个方法就完蛋了(覆写清空)
                raise ValueError("请先调用“create_directory”方法生成存放目录")
            self.message_data_txt = os.path.join(self.message_data_directory, "聊天记录.txt") # 路径拼接
            with open(self.message_data_txt,"w",encoding="utf-8") as messages_txt:   # 创建把“聊天记录”文本文件放置监听到的下消息
                messages_txt.write(f"{datetime.now()}\n时间\发送者\监听数据\n") # 往文件里面写入具体的时间数据
        else:
            try:    # 对输入的路径进行检查
                path = rf"{path}"  # 对输入的路径进行转义
                self.message_data_txt = os.path.join(path, "聊天记录.txt") # 路径拼接
            except OSError:
                raise ValueError("输入的路径不存在，创建txt失败")
            with open(self.message_data_txt, "w", encoding="utf-8") as messages_txt:  # 创建把“聊天记录”文本文件放置监听到的下消息
                messages_txt.write(f"{datetime.now()}\n\t时间\t\t发送者\t\t7监听数据\n")  # 往文件里面写入具体的时间数据()

    def write_txt(self,message_list):
        """追加模式写入监听到的数据
        参数：message_list ：消息列表
        """
        with open(self.message_data_txt, "a", encoding="utf-8") as messages_txt:  # 创建把“聊天记录”文本文件放置监听到的下消息
            for one_message in message_list:
                messages_txt.write(one_message + "\n")  # 换行
            messages_txt.flush()  # 立即写入硬盘（但需注意性能影响）

    def get_messages(self):
        """分割消息的控件数据获得消息
        返回值:
        self.message_list:截获的消息列表
        self.AutomationId_list ： 控件id列表
        self.messages_count ： 最大消息数
        """
        one_message_join =  ""  # 用来存放合成的消息(因为一条消息可以是和合成的)
        def txt_split(obj):
            """递归函数，遍历有效文本控件"""
            try:    # AttributeError: 'NoneType' object has no attribute 'Name'
                nonlocal one_message_join # 用来存放一条消息(因为一条消息可以是和合成的)
                if len(obj.GetChildren()) == 0: # 判断单个控件的内容
                    if obj.LocalizedControlType == "文本" and obj.Name != "":  # 获得有效文本控件的内容
                        one_message_join += obj.Name
                    elif obj.LocalizedControlType == "组" and obj.Name == "表情":  # 确认是有效的表情(如何直接检测Name会导致如果“表情”是文本也会收集)
                        one_message_join += obj.Name # QQ自带的表情
                    elif obj.LocalizedControlType == "图像" and obj.Name == "" and obj.GetParentControl().Name == "表情" and obj.GetParentControl().LocalizedControlType == "组":
                        one_message_join += "表情"    # 父窗口是表情，但是最底层的子控件是图像且Name为空
                    elif obj.LocalizedControlType == "图像" and obj.AriaRole == "img" and obj.Name == "":  # 被引用图像消息体
                        one_message_join += "图像"    # 父窗口是表情，但是最底层的子控件是图像且Name为空
                    elif obj.LocalizedControlType == "图像" and obj.Name == "图片": # 确认是有效的图像(无效的Name为"")
                        one_message_join += "图片、静态或动态表情" # 图片、静态动态表情都被列为图像
                    elif obj.LocalizedControlType == "组" and obj.Name == "视频":
                        one_message_join += obj.Name
                    elif obj.LocalizedControlType == "组" and obj.Name == "卡片":
                        one_message_join += obj.Name
                elif obj.LocalizedControlType == "组" and "语音" in obj.Name:
                    one_message_join = obj.Name # 检测到语音退出语音的遍历
                    return one_message_join # 退出遍历
                else:
                    for children_control in obj.GetChildren():
                        txt_split(children_control)
                return True
            except AttributeError as ex:
                # print(f"文本消息解析失败，{ex}")
                self.output_text = f"文本消息解析失败，{ex}"
                return "获取失败"
        self.messages_count = len(self.message_list_box.GetChildren())  # 更新消息数属性
        # print(f"获得消息数:{messages_count}")
        self.message_list.clear()  # 设置一个列表接收消息(对属性的列表清空)
        self.message_list_dict.clear()  # 清空列表字典
        self.AutomationId_list.clear()  # 用来放置控件的AutomationId(对属性的列表清空)
        # message_child = self.message_list_box.GetChildren()  # 这里多一个变量是为了2次遍历相同的控件
        for message_control in self.message_list_box.GetChildren()    :# 优先遍历控件id动态更改属性
            self.AutomationId_list.append(message_control.AutomationId)  # 放置控件id
        for message_control in self.message_list_box.GetChildren():   # 以下标的形式遍历(方便后续处理)
            try:    # 估计有些消息体确实没有子孩子，或者突然过时了(实际猜测是最新的消息被顶掉了，导致控件为空)
                self.message_list_box.Refind()  # 每次调用都刷新一次控件
                message_control = message_control.GetChildren()[0]  # 进入组控件里面（所有都单个消息控件都得进入）
                pass  # IndexError: list index out of range  提示我下标溢出
                if len(message_control.GetChildren()) == 2: # 如果等于2代表时间被嵌入的
                    message_control = message_control.GetChildren()[1]  # 进入个人消息体里面(避开时间)
                else:
                    message_control = message_control.GetChildren()[0]  # 进入个人消息体里面
                send_name = message_control.GetChildren()[0].Name   # 发送者的名字
                one_message_join = ""  # 清空组合的信息
                if len(message_control.GetChildren()) == 1: # 对方或我撤回了成员的某条消息(撤回、加入群聊)
                    if message_control.GetChildren()[0].GetChildren()[1].Name == "加入了群聊。":
                        send_name = "系统"
                        # 加入者的名字 拼接 message_control.GetChildren()[0].GetChildren()[1].Name（"加入了群聊。"）
                        one_message_join = message_control.GetChildren()[0].GetChildren()[0].Name + "加入了群聊。"    # 人名和群聊
                    elif len(message_control.GetChildren()[0].GetChildren()) == 2:  # 撤回消息的情况
                        send_name = message_control.GetChildren()[0].GetChildren()[0].Name   # 重新定义发送者的名字
                        one_message_join = message_control.GetChildren()[0].GetChildren()[1].Name  # 撤回了一条消息
                    else:
                        send_name = "系统" # 拍一拍的发送者
                        for pai_control in message_control.GetChildren()[0].GetChildren():  # 遍历拍一拍的控件
                            one_message_join += pai_control.Name  # 把拍一拍的消息组合起来
                elif len(message_control.GetChildren()) == 2: # 引用和卡片
                    if message_control.GetChildren()[1].Name == "卡片":
                        one_message_join = "卡片消息"
                    else:   # 引用类型
                        txt_split(message_control)
                elif len(message_control.GetChildren()) == 3:   # 文件类型和普通聊天类型都是3个组，消息内容在第二个组
                    if message_control.GetChildren()[1].GetChildren()[0].Name != "":    # 文件类型
                        one_message_join = message_control.GetChildren()[1].GetChildren()[0].Name   # 文件名
                    elif message_control.GetChildren()[1].GetChildren()[0].Name == "":   # 文本控件在里面
                        txt_split(message_control)
                else:   # 超级复合文本（多个链接之类的）
                    txt_split(message_control)
                self.message_list.append(f"{datetime.now().time().strftime("%H:%M:%S")}" + " " + send_name + ":\t"+one_message_join) # 标准化后将一条消息放到列表里面
                self.message_list_dict.append({"发送者": send_name,"发送消息": one_message_join,"发送时间": datetime.now().time().strftime("%H:%M:%S")})
                # print(f"{datetime.now().time().strftime("%H:%M:%S")}" + "\t" + send_name + ":\t"+one_message_join)
            except IndexError as e:  # 显式捕获IndexError
                # print(f"\033[33m下标溢出：无法获取子控件，原始错误：{e}\033[0m",end="\t")
                # print(f"\033[33m子孩子控件数:{len(message_control.GetChildren())}，文本控件解析失败\033[0m")   # 打控件的子孩子数
                self.output_text = f"标溢出：无法获取子控件，原始错误：{e}\n子孩子控件数:{len(message_control.GetChildren())}，文本控件解析失败"
                continue # 跳过这次控件访问
        return self.message_list, self.AutomationId_list, self.messages_count # 返回截获的消息列表、控件id列表、最大消息数

    def monitor_message(self):
        pass    # 修改逻辑，跳过旧消息的文本控件解析(这里其实是对比上一次消息列表和这次消息列表消息的不同，实际上能在逻辑上实现)
        """消息监听(对比上次的消息控件id来确认添加的消息数)"""
        # old_message_list = self.message_list.copy()   # 保存上一次的消息列表(注意这里是深拷贝)
        pass    # 可以进行消息对比
        old_AutomationId_list = self.AutomationId_list.copy()  # 保存上一次的控件列表(注意这里是深拷贝)
        self.get_messages()  # 更新消息来进行对比(更新消息列表、控件id号、最大消息数)
        """三种情况:
        1. 旧表的下标存在，有新的消息，下标在新表里面但不是新表的最后一个下标
        2. 旧表的下标存在，无新的消息，下标等于新表的最后一个下标
        3. 下标不存在，即为监听的连续性遭到破坏，可能存在监听遗漏
        """
        # 旧表的下标存在，有新的消息，下标在新表里面但不是新表的最后一个下标
        if old_AutomationId_list[-1] in self.AutomationId_list and old_AutomationId_list[-1] != self.AutomationId_list[-1]:
            self.control_id_index = self.AutomationId_list.index(old_AutomationId_list[-1]) + 1  # 新消息的控件id下标(不加1就是最后一个旧消息控件id下标)
            # print("1. 旧表的下标存在，有新的消息，下标在新表里面但不是新表的最后一个下标")
        # 2. 旧表的下标存在，无新的消息，下标等于新表的最后一个下标
        elif old_AutomationId_list[-1] in self.AutomationId_list and old_AutomationId_list[-1] == self.AutomationId_list[-1]:
            self.control_id_index = self.AutomationId_list.index(old_AutomationId_list[-1]) + 1 # 没有新消息的控件下标(等于最新控件最后的下标)[这里的减1是为了不在下面进行遍历]
            # print("2. 旧表的下标存在，无新的消息，下标等于新表的最后一个下标")
        # 3. 下标不存在，即为监听的连续性遭到破坏，可能存在监听遗漏
        elif old_AutomationId_list[-1] not in self.AutomationId_list:
            # 无法对接上旧表的消息下表，可能刚好就是没承接旧表下标但是又刚好没新的消息下标
            self.control_id_index = 0    # 重新遍历新表的消息体
            self.write_txt([f"{datetime.now()}极大可能存在消息监听丢失，开始重新记录"])  # 写入数据(传入列表)
            # print(f"{datetime.now()}极大可能存在消息监听丢失，开始重新记录")
            self.output_text = f"{datetime.now()}极大可能存在消息监听丢失，开始重新记录"
        """原理解析：保存上一次控件获得的消息到临时变量，更新属性后进行对比，通过控件id去判断加入哪些新的消息"""
        new_message_list = list()   # 新列表用来临时放置新消息的元素
        try:  # 估计有些消息体确实没有子孩子，或者突然过时了(实际猜测是最新的消息被顶掉了，导致控件为空)
            for index in range(self.control_id_index,self.messages_count):
                # print(index)
                new_message_list.append(self.message_list[index])
                message_dict = self.message_list_dict[index]   # 我还是增强可读性和减少引用吧
                self.hook_message(message_dict)         # 截获关键消息(关键词回复)
            self.message_list = new_message_list # 把新消息的列表给消息列表属性(之前的空间都被垃圾回收机制回收掉)

            # for one_message in self.message_list:   #输出监听到的消息
                # print(one_message)

            self.write_txt(self.message_list)   # 写入数据

            # 修改之前的消息解析输出的方案(输出重定向)
            return "\n".join([one_message for one_message in self.message_list])
        except IndexError as e:  # 显式捕获IndexError
            # print(f"\033[93mmonitor_message下标溢出：无法获取子控件，原始错误：{e}\033[0m",end="\t")
            # print(f"\033self.message_list子孩子控件数:{len(self.message_list)}\033[0m")  # 打控件的子孩子数
            self.output_text = f"mmonitor_message下标溢出：无法获取子控件，原始错误：{e}\nself.message_list子孩子控件数:{len(self.message_list)}"

    def keyword_read(self):
        """关键词读取和正则化处理(读取当前目录下的“关键词回复”文件夹下的文件录入关键字)
        返回值：True
        """
        try:
            with open("用户设置/关键词回复/发送者及其关键词.json", "r", encoding="utf-8") as json_file:
                self.message_sender_keyword = json.load(json_file)  # 监测指定的人和关键字
        except json.JSONDecodeError as e:
            print(f"\033[91mjson文件的格式错误或json没有任何内容\033[0m")
        # 消息关键词内容读入(去除首尾空白判断是否分割内容)
        with open("用户设置/关键词回复/消息关键词.txt", "r", encoding="utf-8") as message_keyword_file:
            if content := message_keyword_file.read().strip():  # 使用海象运算符简化代码
                self.message_keyword = content.split("、")
            else:
                self.message_keyword = []  # 文件为空时返回干净的空列表
        # 发送者关键词内容读入(去除首尾空白判断是否分割内容)
        with open("用户设置/关键词回复/发送者关键词.txt", "r", encoding="utf-8") as sender_keyword_file:
            if content := sender_keyword_file.read().strip():  # 使用海象运算符简化代码
                self.sender_keyword = content.split("、")
            else:
                self.sender_keyword = []  # 文件为空时返回干净的空列表
        # 指定过滤的发送者的消息，不对该发送者的消息进行处理
        with open("用户设置/关键词回复/过滤发送者关键词.txt", "r", encoding="utf-8") as sender_keyword_file:
            if content := sender_keyword_file.read().strip():  # 使用海象运算符简化代码
                self.filter_sender_keyword = content.split("、")
            else:
                self.filter_sender_keyword = []  # 文件为空时返回干净的空列表
        # 判断是否有关键词存在，存在就开启关键词自动回复
        if any([self.message_keyword, self.sender_keyword, self.message_sender_keyword, self.filter_sender_keyword]):
            self.keyword_respond = True   # 开启关键词自动回复
        # 发送者及其关键词的正则处理
        if self.message_sender_keyword:     # 存在关键词才处理(如果不加就会导致如果关键词为空则匹配所有)
            for sender_name in self.message_sender_keyword:  # 遍历键（发送者的名字）
                message_keyword = self.message_sender_keyword[sender_name]  # 获取发送者关键词列表(为了转正则)
                # 安全转为正则表达式，把键值替换为正则对象
                self.message_sender_keyword[sender_name] = re.compile(r'|'.join(map(re.escape, message_keyword)))
        # 消息关键词的处理
        if self.message_keyword:        # 存在关键词才处理(如果不加就会导致如果关键词为空则匹配所有)
            self.message_keyword = re.compile(r'|'.join(map(re.escape, self.message_keyword)))  # 安全转为正则表达式
        # 发送者关键词的处理
        if self.sender_keyword:         # 存在关键词才处理(如果不加就会导致如果关键词为空则匹配所有)
            self.sender_keyword = re.compile(r'|'.join(map(re.escape, self.sender_keyword)))  # 安全转为正则表达式
        # 过滤发送者关键词处理
        if self.filter_sender_keyword:  # 存在关键词才处理(如果不加就会导致如果关键词为空则匹配所有)
            self.filter_sender_keyword = re.compile(r'|'.join(map(re.escape, self.filter_sender_keyword)))  # 安全转为正则表达式
        # print(f"发送者及其关键词:{self.message_sender_keyword}")
        # print(f"消息关键词:{self.message_keyword}")
        # print(f"发送者关键词:{self.sender_keyword}")
        # print(f"过滤发送者关键词:{self.filter_sender_keyword}")
        return True

    def message_keyword_jude(self, text):
        """消息关键词判断(拿到正则表达式对象)
        参数 ： text : 需要判断的文本
        返回值： 如果有消息有关键词就返回True，否则为False
        """
        # 先判断是否为列表(没有设置关键词)，再判断是否存在关键词
        return bool(self.message_keyword.findall(text)) if not isinstance(self.message_keyword, list) else False

    def sender_keyword_jude(self, sender_name):
        """关键发送者判断(拿到正则表达式对象)
        参数 ： sender_name : 发送者的名字
        返回值： 如果有消息有关键词就返回True，否则为False
        """
        # 先判断是否为列表(没有设置关键词)，再判断是否存在关键词
        return bool(self.sender_keyword.findall(sender_name)) if not isinstance(self.sender_keyword, list) else False

    def message_sender_keyword_jude(self, sender_name, text):
        """高级关键词判断(指定发送者加关键词、拿到正则表达式对象)
        参数 : sender_name : 发送者的姓名
        text : 需要判断的文本
        返回值：先判断是否为字典，如果是字典就代表设置了关键发送者，如果不是直接返回False。判断是字典后如果关键词有才返回True
        """
        # 判断人是否在字典里面再是否存在判断关键词
        return (sender_name in self.message_sender_keyword and self.message_sender_keyword[sender_name].findall(text)) if isinstance(self.message_sender_keyword, dict) else False

    def fiter_keyword_jude(self, sender_name):
        """过滤关键词判断
        参数 : sender_name : 发送者的姓名
        返回值：如果排除发送者关键词没有该发送者就直接返回False,有则进入关键词判断，如果有才返回True
        """
        # 如果有限制就去掉限制
        return bool(self.filter_sender_keyword.findall(sender_name)) if not isinstance(self.filter_sender_keyword, list) else False

    def hook_message(self,message_dict,max_processing_queues=10):
        """设置需要截获的消息,可以是发送者，时间，发送消息的内容
        参数： message_dict ： 单条消息字典{"发送者": "yan di fei","发送消息": "hello world","发送时间": "10:10:20"}
        max_processing_queues : 默认10，最大处理队列，超过队列最大数就不进队了
        """
        if len(self.message_processing_queues) > max_processing_queues: # 超出最大处理数
            self.output_text = f"超出消息最大处理数:{max_processing_queues}，不对消息进行处理"
            # print(f"\033[91m超出消息最大处理数:{max_processing_queues}，不对消息进行处理\033[0m")  # 亮红色
            message_dict["发送者"], message_dict["发送消息"] = "系统", f"超出消息最大处理数:{max_processing_queues}，不对消息进行处理"
            """正规定模块"""
        # 截获自己被@的情况做出消息处理（"@名字 "），注意@后是有空格的
        elif f"@{self.monitor_name} " in message_dict["发送消息"]:  # 最新列表获取消息
            # 在这个类之外处理死循环的问题，保留自己的所有名
            self.output_text = f"我被{message_dict["发送者"]}艾特了，消息是:{message_dict["发送消息"]}"
            # print(f"\033[94m我被{message_dict["发送者"]}艾特了，消息是:{message_dict["发送消息"]}\033[0m")
        # 检查是否开启了关键词自动回复,仅当开启了才会
        # 关键词触发需要3个条件：1.设置了关键词2.消息体存在关键词3.消息体的发送者不是自己
        elif not self.keyword_respond or message_dict["发送者"] == self.monitor_name:
            return True   # 没有开启关键词自动回复直接退出
        # 检查是否为排除对象
        elif self.fiter_keyword_jude(message_dict["发送者"]):   # 正则判断是否为排除的发送者
            self.output_text = f"排除对{message_dict["发送者"]}的消息处理"
            # print(f"\033[95m排除对{message_dict["发送者"]}的消息处理\033[0m")  # 亮紫色
            return True   # 存在排除的发送者直接返回退出
        # 截获指定的消息（关键词）进行处理
        elif self.message_keyword_jude(message_dict["发送消息"]):   # 正则判断消息(如果发送者是自己就过滤关键词触发)
            self.output_text = f"截获关键词消息:{message_dict["发送消息"]}，发送者是:{message_dict["发送者"]}"
            # print(f"\033[94m截获关键词消息:{message_dict["发送消息"]}，发送者是:{message_dict["发送者"]}\033[0m")
        # 截获指定发送者存在关键词的消息进行处理(发送者全名在字典你面，发送者的关键词在消息体里面)
        elif self.message_sender_keyword_jude(message_dict["发送者"], message_dict["发送消息"]):     # 正则判断发送者及其消息(如果发送者是自己就过滤关键词触发)
            self.output_text = f"截获发送者:{message_dict["发送者"]}，消息是:{message_dict["发送消息"]}"
            # print(f"\033[94m截获发送者:{message_dict["发送者"]}，消息是:{message_dict["发送消息"]}\033[0m")
        # 截获指定的发送者进行处理
        elif self.sender_keyword_jude(message_dict["发送者"]):     # 正则判断发送者(如果发送者是自己就过滤关键词触发)
            self.output_text = f"截获关键发送者:{message_dict["发送者"]}，发送消息是:{message_dict["发送消息"]}"
            # print(f"\033[94m截获关键发送者:{message_dict["发送者"]}，发送消息是:{message_dict["发送消息"]}\033[0m")
        # 不满足截获规则
        else:
            return True # 直接返回True避免触发下面的加入消息队列

        # 加入消息队列,加入消息队列后不需要重置标志，因为这是基本数据类型在此方法中会自动重置
        self.message_processing_queues.append(message_dict)  # 加入消息处理队列
        return True

if __name__ == '__main__':
    # chat_win = QQMessageMonitor("Q群号", "Q群中你的名字")
    # chat_win.move()     # 把窗口移动到最上角
    # print(f"数据存放路径:\t{chat_win.message_data_txt}")
    # for one_message in chat_win.message_list:  # 打印初次绑定后的消息
    #     print(one_message)
    # while True:
    #     sleep(0.5)   # 每1秒监测一次变化(0.5防止遗漏)
    #     chat_win.monitor_message() # 开始监控
    #     chat_win.show_win()    # 展示窗口
    #     chat_win.top_win()     # 置顶窗口 zA
    # print("可以输出没有语法错误")

    chat_win = QQMessageMonitor("1","爱丽丝",3)
    # chat_win.send_message("1")
    # chat_win.send_url_image("https://t.alcy.cc/moe")
    chat_win.paste_send_file()