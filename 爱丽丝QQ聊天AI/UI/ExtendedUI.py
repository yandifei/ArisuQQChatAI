"""扩展UI
为了更好实现其他控件逻辑（非基础控件）
"""
# 系统自带
import os
import platform  # CPU逻辑核心计算
import sys
# 第三方
import keyring                                                                              # api密钥加密和解密
import psutil                                                                               # 电脑硬件信息获取
import requests                                                                             # 网络请求
from PyQt6.QtCore import QUrl, pyqtSlot                                                     # 链接非图片的资源文件
from PyQt6.QtCore import Qt, QTimer, QThreadPool                                            # Qt的核心类
from PyQt6.QtGui import QDesktopServices, QShortcut, QKeySequence                           # 桌面服务
from PyQt6.QtMultimedia import QMediaPlayer                                                 # 视频播放器
from PyQt6.QtWidgets import QApplication, QMessageBox, QGroupBox, QVBoxLayout, QTextBrowser # 界面处理类
# 自己的包
try:  # 实际环境使用
    from .functions import OutputRedirection, clear_temp, InputRedirection                  # 导入非UI功能函数
    from .arisu_qq_chat_ai_ui import ArisuQQCHatAIUI                                        # 基础框架的类
except (ModuleNotFoundError, ImportError):                                                  # 测试环境使用
    from functions import OutputRedirection, clear_temp, InputRedirection                   # 导入非UI功能函数
    from arisu_qq_chat_ai_ui import ArisuQQCHatAIUI                                         # 基础框架的类
    from UI.arisu_qq_chat_ai_core import ArisuQQChatAICore                                  # 外部方法的类
    from deepseek_conversation_engine import DeepseekConversationEngine                     # AI对话
    from qq_message_monitor import QQMessageMonitor                                         # QQ监控
from 用户设置.configuration_manager import ConfigurationManager                             # 导入配置文件的类
from arisu_logger import debug, info, warning, critical, exception                          # 导入日志方法
from arisu_logger import console_handler                                                    # 导入日志处理器
from UI.arisu_threading import ArisuThreading                                               # 线程的类
from resources.Arisu import Ui_Arisu                                                        # uic转后py文件
import resources.resources                                                                  # 这个qrc必须存在（即使编译器报灰色）
debug("ExtendedUI.py(UI界面额外扩展文件已加载完成)")


# 可以通过多继承去调用uic转后py文件, Ui_Arisu
# class ArisuUI(ArisuQQCHatAIUI):
class ArisuUI(Ui_Arisu, ArisuQQCHatAIUI):
    def __init__(self, title="", show_system_tray=True, ui_file_path="../resources/Arisu.ui"):
        """构建一个无标题栏（自定义）的窗口
        title : 窗口标题（默认为""）
        show_system_tray : 是否展示系统托盘（False/True）,默认为True
        ui_file_path : "../resources/Arisu.ui"开发中ui文件的路径
        """
        super().__init__(title, show_system_tray, ui_file_path)  # 继承父类的属性和方法
        """终端输入输出重定向"""
        # 日志输出重定向
        log_output_redirection = OutputRedirection()  # 实例化输出重定向对象
        console_handler.stream = log_output_redirection  # 日志输出重定向
        log_output_redirection.text_print.connect(self.log_print)  # 信号连接
        info("日志输出重定向已完成")
        # 准输出重定向
        stdout_redirection = OutputRedirection()  # 实例化输出重定向对象
        sys.stdout = stdout_redirection  # 标准输出重定向
        stdout_redirection.text_print.connect(self.log_print)  # 信号连接
        info("准输出重定向已完成")
        # 错误输出重定向
        stderr_redirection = OutputRedirection()  # 实例化输出重定向对象
        sys.stderr = stderr_redirection  # 错误输出重定向
        stderr_redirection.text_print.connect(self.log_print)  # 信号连接
        # 输入重定向
        sys.stdin = InputRedirection(self)
        # 隐藏终端输入输出重定向窗口
        self.ConsoleWidget.hide()
        info("已隐藏终端输入输出重定向窗口")
        """配置文件数据初始化"""
        self.config = ConfigurationManager()  # 实例化配置文件(读取配置文件数据)
        info("用户配置信息已导入UI列表视图")
        """=====================================================额外界面功能撰写=================================================="""
        """导航栏"""
        self.ModeWidget.tabBarClicked.connect(lambda: QTimer.singleShot(1, self.window_shaking))  # 导航栏事件修复动态视频位移bug
        self.ModeWidget.setCurrentIndex(self.config.user_settings["初始界面位置"].getint("init_index"))  # 设置初始界面位置
        self.InitialInterfaceLocationComboBox.setCurrentIndex(self.config.user_settings["初始界面位置"].getint("init_index"))  # 设置下拉框位置
        self.tab_bar = self.ModeWidget.tabBar()  # 获得标签栏（为后面标签栏功能做铺垫）
        self.set_navigation_bar_sorting()  # 导航栏设置为用户界面位置
        self.tab_bar.tabMoved.connect(self.on_tab_moved)  # 连接标签页面移动的信号（实现标签也移动后的记录）
        self.InitialInterfaceLocationComboBox.activated.connect(self.initial_interface_location_selector)  # 初始界面选择下拉框（录入ini）
        info("导航栏初始化完成")
        """Home（主页）"""
        # 动态壁纸
        self.video_player = QMediaPlayer(self)                                                      # 创建多媒体播放器
        self.video_player.setVideoOutput(self.DynamicBackground)                                    # 多媒体播放器设置窗口来视频输出
        self.video_player.setSource(QUrl("qrc:/背景/背景/动态视频.mp4"))                             # 设置播放资源，fromLocalFile处理路径问题
        self.DynamicBackground.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatioByExpanding)    # 保持宽高比并填充整个控件
        self.video_player.setLoops(QMediaPlayer.Loops.Infinite)                                     # 循环无限次数
        self.video_player.play()                                                                    # 开始播放
        info("动态壁纸加载完毕")
        # 功能按钮
        self.Function1.clicked.connect(self.start_auto_reply)   # 一键开启
        self.Function2.clicked.connect(self.home_jumps_bind)    # 基础配置(主页跳转到绑定界面)
        self.Function3.clicked.connect(self.open_document)      # 文档链接
        self.Function4.clicked.connect(self.link_to_github)     # Star
        """状态监测"""
        # ==================Q群绑定==================
        self.import_bind_data()                                                 # 导入绑定信息(加载Q群列表的配置信息)
        self.AddOrChangeQQGroup.clicked.connect(self.add_or_change_qq_group)    # 添加或修改QQ群按钮
        self.RemoveQQGroup.clicked.connect(self.remove_qq_group)                # 移除QQ群按钮
        self.SwitchReply.clicked.connect(self.switch_reply)                     # AI自动回复开关
        self.QQGroupList.currentItemChanged.connect(self.show_qq_group_info)    # QQ群列表选择项发生改变时显示Q群信息
        self.QQGroupList.clicked.connect(self.show_qq_group_info2)              # QQ群列表选择项被点击时显示Q群信息
        self.previous_item = None                                               # 用来记录上一个被点击的选择项
        self.QQGroupList.itemClicked.connect(self.item_clicked)                 # 选择项被点击，处理取消选中
        info("状态检测界面加载完毕")
        """键盘快捷键"""
        # 文档和项目地址链接
        self.shortcut = QShortcut(QKeySequence("F1"), self)
        self.shortcut.activated.connect(self.hotkey_github_doc)
        # 开启/关闭爱丽丝的AI自动回复
        self.shortcut = QShortcut(QKeySequence("F12"), self)
        self.shortcut.activated.connect(self.switch_reply)
        # 开启动态主页
        self.shortcut = QShortcut(QKeySequence("F8"), self)
        self.shortcut.activated.connect(self.hotkey_dynamic_background_create)
        # 关闭动态主页
        self.shortcut = QShortcut(QKeySequence("F7"), self)
        self.shortcut.activated.connect(self.hotkey_dynamic_background_del)
        # 全屏/不全屏
        self.shortcut = QShortcut(QKeySequence("F11"), self)
        self.shortcut.activated.connect(self.hotkey_switch_full_screen)
        # 显示/隐藏输入输出重定向窗口
        self.shortcut = QShortcut(QKeySequence("F9"), self)
        self.shortcut.activated.connect(self.console_widget_visible)
        # 打开一个cmd窗口
        self.shortcut = QShortcut(QKeySequence("F10"), self)
        self.shortcut.activated.connect(self.open_cmd)
        """用户设置"""
        self.ConsoleWidget.document().setMaximumBlockCount(100)                 # 设置重定向窗口最多为20行，多的自动删除
        self.tip_api_key_exist()                                                # 告诉用户密钥是否存在
        self.tip_logic_cpu_count()                                              # 提示用户可以使用的逻辑CPU数量，并自动计算最合适的CPU数量
        self.RestoreNavigationBarSortingButton.clicked.connect(self.restore_navigation_bar_sorting)  # 还原导航栏排序按钮
        self.APIKeyConfirm.clicked.connect(self.__api_key_confirm)              # 检测api有效和把deepseek注入到系统变量
        self.LogicCPUCountConfirm.clicked.connect(self.logic_cup_confirm)       # 确认逻辑CPU数
        self.OpenRoleDir.clicked.connect(self.open_role_repository_directory)   # 打开人设仓库目录
        self.KeywordReplyDir.clicked.connect(self.open_keyword_reply_directory) # 打开关键词回复目录
        self.JMDownloadStrategy.clicked.connect(self.open_jm_strategy_file)     # 打开JM策略的配置文件
        self.LogQueryDir.clicked.connect(self.open_log_directory)               # 打开日志文件夹
        self.Uninstall.clicked.connect(self.uninstall)                          # 卸载按钮
        """后端核心"""
        # 开启了自动回复的标志
        self.arisu_auto_reply_flag = False
        # 放置输出窗口容器的对象列表，直接删除父容器（QGroupBox）是最简单且最安全的做法)
        self.output_groupBox_list = list()
        # 放置创建进程的参数列表
        self.thread_args_list: list[tuple] = []
        # 线程池
        self.thread_pool = QThreadPool()  # 私有线程池而非全局线程池
        self.running_threads: list[ArisuThreading] = list()  # 正在运行的线程(线程崩溃只要修改这里面的线程就行)
        """程序结束（界面被关闭）"""
        # arisu.aboutToQuit.connect(lambda: info("软件退出,日志停止记录"))     # 连接UI界面退出信号

    """=====================================重构后基础布局以外的内容============================================="""
    """输出重定向"""
    def log_print(self, text):
        """输出
        text : 重定向返回的文本
        """
        # 文本不为空才发送，即使是"\t"也不算空，为了过滤print的二次"\n",所以这里也就把（text == "\n"）给过滤掉
        if text:
            self.ConsoleWidget.append(text)

    """导航栏"""
    def set_navigation_bar_sorting(self):
        """把导航栏按钮顺序设置为用户界面位置"""
        location = self.config.user_interface_location()  # 从配置文件里面拿到用户界面位置(最后一次导航栏的位置)
        tab_widget = [self.ModeWidget.widget(index) for index in range(self.ModeWidget.count())]  # 读取标签页的所有界面
        for widget in tab_widget:
            # 找到当前遍历标签页的下标->从配置文件的字典中找到设置好的下标->根据当前的下表移动到设置位置的下标
            self.tab_bar.moveTab(self.ModeWidget.indexOf(widget), int(location[widget.objectName()]))

    def on_tab_moved(self, from_index, to_index):
        """选项卡被用户移动到了不同的位置的事件
        实现记录导航栏排序（写入硬盘）
        """
        print(f"标签页从位置 {from_index} 移动到了位置 {to_index}")
        # 定义字典映射用来转化ui控件的类名和配置的键名
        transform_dict = {"Home": "主页", "StateMonitor": "状态监测", "KeyboardShortcut": "热键", "QuestionLinks": "问题链接",
                          "Settings": "用户设置"}
        tab_widget = [self.ModeWidget.widget(index) for index in range(self.ModeWidget.count())]  # 读取标签页的所有界面
        for widget in tab_widget:  # 遍历界面
            # 界面下标写入到ini配置中(写入的必须是字符串类型)
            self.config.user_settings["用户界面位置"][transform_dict[widget.objectName()]] = str(
                self.ModeWidget.indexOf(widget))
        # print(self.config.user_interface_location())
        self.config.save_user_settings_ini()  # 更新用户设置ini配置写入硬盘中

    def window_shaking(self):
        """导航栏事件修复动态视频位移bug"""
        width, height = self.size().width(), self.size().height()
        self.resize(width, height + 1)  # 加1点像素
        self.resize(width, height)  # 恢复大小（通过改变边框的方法实现动态背景显示不完整的问题）

    """主页"""
    def start_auto_reply(self):
        """一键开启按钮槽函数(开启自动回复)"""
        # 判断是否开启了自动跳转
        if not self.arisu_auto_reply_flag:  # 没有开启跳转就进行校验开启
            info("点击了一键开启，检测到未开启AI自动回复，开始AI自动回复的逻辑代码")
            # 执行自动回复逻辑并判断是否开启了
            if self.create_state_monitor():  # 执行核心指令(AI自动回复)
                # 按钮样式切换为关闭按钮（成功开启才改变按钮样式）
                self.SwitchReply.setText("关闭自动回复")
                self.SwitchReply.setStyleSheet("""
                QPushButton{border-radius: 10px;border-width:3px;border-color: rgb(255,0,0);
                border-style: solid;color: rgb(255,0,0);background-color: rgba(255,0,0,0.1);}
                QPushButton::hover{background-color: rgba(255,0,0,0.5);color: rgb(255, 255, 255);}
                QPushButton:pressed {background-color: rgb(255,0,0);color: rgb(255, 255, 255);}
                """)
            else:
                # 按钮样式切换为开启按钮
                self.SwitchReply.setText("开启自动回复")
                self.SwitchReply.setStyleSheet("""
                QPushButton{border-radius: 10px;border-width:3px;border-color: rgb(0,85,255);
                border-style: solid;color: rgb(0,85,255);background-color: rgba(0,85,255,0.1);}
                QPushButton::hover{background-color: rgba(0,85,255,0.5);color: rgb(255, 255, 255);}
                QPushButton:pressed {background-color: rgb(0,85,255);color: rgb(255, 255, 255);}
                """)

        else:
            # 已经开启了自动回复直接跳转界面
            info("点击了一键开启，但已开启了AI自动回复，自动跳转到监测界面")
            self.jump_state_output_widget()

    def home_jumps_bind(self):
        """基础配置按钮(主页跳转到绑定界面)"""
        if self.jump_bind_widget():
            info("点击了基础配置按钮主页成功跳转到了绑定界面")

    def open_document(self):
        """文档链接按钮槽函数实现"""
        # 判断文件是否存在和打开文档
        try:
            if os.path.isfile(r".\文档\爱丽丝QQ聊天AI.pdf"):  # 实际开发路径
                os.startfile(r".\文档\爱丽丝QQ聊天AI.pdf")  # 打开文档，注意路径符号
                info("使用开发路径后文档打开了")
            elif os.path.isfile(r"..\文档\爱丽丝QQ聊天AI.pdf"):  # 当前测试路径
                os.startfile(r"..\文档\爱丽丝QQ聊天AI.pdf")  # 打开文档，注意路径符号
                info("使用测试路径后文档打开了")
            else:
                exception("文档不存在")
                print("文档不存在")
                # 错误弹窗提示
                QMessageBox.critical(self, "错误提示", "文档不存在", QMessageBox.StandardButton.Ok,
                                     QMessageBox.StandardButton.Ok)
                warning("文档不存在，可能被删除了")
        # 异常处理
        except Exception as e:
            # print(f"打开文档失败: {str(e)}")  # 输出错误信息
            QMessageBox.critical(self, "错误提示", str(e), QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.Ok)
            exception("文档打开失败")
            print("文档打开失败")

    @staticmethod
    def link_to_github():
        """链接跳转到github"""
        QDesktopServices.openUrl(QUrl("https://github.com/yandifei/ArisuQQChatAI"))
        info("已条跳转链接到Github项目地址")

    """状态设置"""
    def jump_state_output_widget(self):
        """跳转到状态输出界面"""
        # 跳到状态监测界面（设置当前选项卡的界面，从配置文件里面拿到数据，需要类型转换）
        self.ModeWidget.setCurrentIndex(int(self.config.user_settings["用户界面位置"]["状态监测"]))
        # 读取状态监测选项卡的所有选项卡界面（为什么这么麻烦？因为这个选项卡是可以变动位置的，无法靠固定下标定位）
        tab_widget = [self.StateTabWidget.widget(index) for index in range(self.StateTabWidget.count())]
        for widget in tab_widget:  # 遍历界面
            # 找到状态输出的界面进行跳转
            if widget.objectName() == "StateOutput":
                self.StateTabWidget.setCurrentWidget(widget)  # 跳转到Q群绑定界面
                return True  # 跳出循环
        else:  # 不可能找不到这个界面，除非篡改ui删了这个界面不然这里不可能有异常
            warning("没有成功跳转到状态输出。问题出现源：\n")
        return False

    def jump_bind_widget(self):
        """转到绑定界面"""
        # 设置当前选项卡的界面（从配置文件里面拿到数据，需要类型转换）
        self.ModeWidget.setCurrentIndex(int(self.config.user_settings["用户界面位置"]["状态监测"]))
        # 读取状态监测选项卡的所有选项卡界面（为什么这么麻烦？因为这个选项卡是可以变动位置的，无法靠固定下标定位）
        tab_widget = [self.StateTabWidget.widget(index) for index in range(self.StateTabWidget.count())]
        for widget in tab_widget:  # 遍历界面
            # 找到Q群绑定的界面进行跳转
            if widget.objectName() == "Bind":
                self.StateTabWidget.setCurrentWidget(widget)  # 跳转到Q群绑定界面
                return True  # 跳出循环
        else:  # 不可能找不到这个界面，除非篡改ui删了这个界面不然这里不可能有异常
            warning("没有成功跳转到绑定界面。问题出现源：\n")
        return False

    def add_state_monitor(self, qq_group_name: str, bot_name: str, root: str, exit_password: str, init_role: str,
                          qq_group_location: str, remove_dangerous_order: str):
        """添加状态监视器
        参数：
        qq_group_name ：QQ群名
        bot_name ：机器人名
        root ：最高权限者
        exit_password ：退出指令的密码
        init_role ：初始人设
        qq_group_location ：0,0（窗口的位置，文本的形式）
        remove_dangerous_order ：False（布尔值）
        返回值：
        group_box ： 创建的容器对象
        text_browser ： 创建的文本浏览器对象
        """

        # 设置容器
        group_box = QGroupBox(qq_group_name)  # 设置容器标题为QQ群名
        group_box.setObjectName(qq_group_name)  # 设置容器类名为QQ群名
        group_box.setMinimumWidth(600)  # 设置容器最小宽度（600是必须的，为了好看）
        group_box_layout = QVBoxLayout(group_box)  # 设置GroupBox的内部为垂直布局
        group_box_layout.setContentsMargins(0, 20, 0, 7)  # 设置内容边距
        group_box.setStyleSheet(  # 设置容器样式
            """/* 主框体样式 */
            QGroupBox {
                border-radius: 10px;		/*圆角*/
                border: 2px solid rgb(,0,0,0);  /*边框大小、边框类型、边框颜色*/
                background-color: rgb(255, 255, 255);	/*背景颜色为白色*/
                font-size: 20px;             /* 字体大小(影响标题)*/
                 font-weight: bold;          /* 字体加粗 */
                margin-top: 1.4ex;          /* 标题上方空间 (重要!) */
            }
             /* 标题样式 */
            QGroupBox::title {
                subcontrol-origin: margin;   /* 定位基准 */
                subcontrol-position: top center; /* 位置: 顶部居中 */
                background-color: rgb(255, 255, 255);		/*标题背景*/
                border: 4px double rgb(65, 65, 220);  /*边框大小、边框类型、边框颜色*/
            }""")
        # 创建TextBrowser并初始样式
        text_browser = QTextBrowser()
        text_browser.setObjectName(f"{qq_group_name}_output")  # 设置TextBrowser类名为 QQ群名_output
        text_browser.setStyleSheet(
            """/* 主窗口样式 */
            QTextBrowser {
                background-color: rgb(255, 255, 255);   /*白色背景*/   
                border: none;                           /*无边框*/
                font-size: 20px;                        /* 字体大小 */
                color: rgb(128, 128, 128);              /*字体颜色为灰色*/
            }
            
            /* 滚动条 - 垂直 */
            QTextBrowser QScrollBar:vertical {
                border-radius:10px;                 /*圆角*/
                background-color: rgb(255,255,255); /*背景颜色*/
                width: 4px;                         /* 滚动条默认宽度*/
            }
            
            /* 垂直滚动条滑块 */
            QTextBrowser QScrollBar::handle:vertical {
               border-radius:3px;                   /*圆角*/
                background-color: rgb(0, 255, 255); /*背景颜色*/
            }
            
            /* 垂直滚动条滑块悬停 */
            QTextBrowser QScrollBar::handle:vertical:hover {
                background-color: rgba(0, 255, 255,0.5);/*背景颜色*/
            }
            
            /* 滚动条向上按钮 */
            QTextBrowser QScrollBar::sub-line:vertical {	
                height: 0px; /*设置按钮大小为0(不显示)*/
            }
            
            /* 滚动条向下按钮 */
            QTextBrowser QScrollBar::add-line:vertical {
                height: 0px; /*设置按钮大小为0(不显示)*/
            }
            
            /* 滚动条背景 */
            QTextBrowser QScrollBar::add-page:vertical, 
            QTextBrowser QScrollBar::sub-page:vertical {
                background: none;		/*没有背景,之前是网格*/
            }""")
        # 将TextBrowser添加到GroupBox布局中
        group_box_layout.addWidget(text_browser)
        # 添加GroupBox到滚动窗口中(这里必须在布局器里面添加)
        self.StateWidgetLayout.addWidget(group_box)
        info(
            f"成功创建并添加状态监视器:{group_box.objectName()}\n监控数据输出对象(输出重定向):{text_browser.objectName()}")

        def put_text(msg: str):
            """输入文本到文本浏览器+换行"""
            text_browser.insertPlainText(f"{msg}\n")

        # 文本浏览器添加初始化文本
        put_text(f"QQ群名:{qq_group_name}")
        put_text(f"机器人名:{bot_name}")
        put_text(f"最高权限者:{root}")
        put_text(f"退出指令的密码:{exit_password}")
        put_text(f"初始人设:{init_role}")
        put_text(f"QQ群窗口库位置:{qq_group_location}")
        if remove_dangerous_order == "True":
            put_text("危险指令移除:是")
        else:
            put_text("危险指令移除:否")
        # text_browser.insertPlainText()
        # text_browser.insertPlainText(f"机器人名:{bot_name}")
        # text_browser.insertPlainText(f"最高权限者:{root}")
        # text_browser.insertPlainText(f"退出指令的密码:{exit_password}")
        # text_browser.insertPlainText(f"初始人设:{init_role}")
        # text_browser.insertPlainText(f"QQ群窗口库位置:{qq_group_location}")
        # if bool(remove_dangerous_order):
        #     text_browser.insertPlainText("危险指令移除:是")
        # else:
        #     text_browser.insertPlainText("危险指令移除:否")
        return group_box, text_browser

    def import_bind_data(self):
        """导入绑定信息(加载Q群列表的配置信息)"""
        # 拿到绑定ini的所有节
        for section in self.config.bind.sections():
            self.QQGroupList.addItem(section)  # 把所有节都添加到列表中
        info("导入之前绑定的Q群信息到列表完毕")

    def add_or_change_qq_group(self):
        """添加或修改qq群槽函数实现
        录入Q群绑定信息(7个数据)
        """
        before_add = self.config.bind.sections()  # 添加前的所有节
        # 校验输入值(前4个输入值不能为空，高效版)
        if not all(field.text() for field in (self.QQGroupName, self.BotName, self.Root, self.ExitPassword)):
            # 必要输入为空
            self.QQGroupName.setPlaceholderText("Q群名不能为空")
            self.BotName.setPlaceholderText("机器人名不能为空")
            self.Root.setPlaceholderText("最高权限者不能为空")
            self.ExitPassword.setPlaceholderText("退出指令密码不能为空")
            return False
        else:
            # 判断人设是否存在
            if not self.check_role_exist(self.InitRole.text()): return False
            # 判断窗口坐标输入是否有效
            if not self.check_qq_group_location_input(self.QQGroupLocation.text()): return False
            # 添加新节和键值(字典形式)
            self.config.bind[self.QQGroupName.text()] = {  # 直接通过字典赋值创建节和键值
                "bot_name": self.BotName.text(),
                "root": self.Root.text(),
                "exit_password": self.ExitPassword.text(),
                "init_role": self.InitRole.text() if self.InitRole.text() else "爱丽丝",
                "qq_group_location": self.QQGroupLocation.text(),
                "remove_dangerous_order": str(self.RemoveDangerousOrder.isChecked())  # 布尔值要转为字符串
            }
            # 把新的选择项添加进入Q群列表，可以确保不重复
            for section in before_add:  # 遍历添加前的节看是否重复
                if section == self.QQGroupName.text():
                    info(f"已修改QQ群的相关项:{section}")
                    break  # 重复了退出循环
            # 没有重复添加进去（重复的节不需要再次添加到列表里面去）
            else:
                info(f"已成功添加新QQ群相关项:{self.QQGroupName.text()}")
                self.QQGroupList.addItem(self.QQGroupName.text())  # 把新的选择项目添加到列表中
                self.QQGroupList.scrollToBottom()  # 滚到底部让用户知道它添加成功了
            # 保存Q群绑定的文件(无论是否重复都要)
            self.config.save_bind_ini()
            self.set_orign_tip()  # 输入框设置回正常的提示
        return True

    def remove_qq_group(self):
        """移除QQ群按钮槽函数实现"""
        # 用选中的选择项才移除
        if self.QQGroupList.currentRow() != -1:
            # 优先删除键值后删除当前选择项，不然会导致删除的是删除项后当前项
            self.config.bind.remove_section(self.QQGroupList.currentItem().text())  # 绑定配置删除对应的节
            self.config.save_bind_ini()  # 写入硬盘
            self.QQGroupList.takeItem(self.QQGroupList.currentRow())  # 删除当前选中项

    def switch_reply(self):
        """自动回复开关槽函数实现"""
        # 需要关闭自动回复的情况
        if self.SwitchReply.text() == "关闭自动回复":
            # 按钮样式切换为开启按钮
            self.SwitchReply.setText("开启自动回复")
            self.SwitchReply.setStyleSheet("""
                        QPushButton{border-radius: 10px;border-width:3px;border-color: rgb(0,85,255);
                        border-style: solid;color: rgb(0,85,255);background-color: rgba(0,85,255,0.1);}
                        QPushButton::hover{background-color: rgba(0,85,255,0.5);color: rgb(255, 255, 255);}
                        QPushButton:pressed {background-color: rgb(0,85,255);color: rgb(255, 255, 255);}
                        """)
            """开始关闭逻辑"""
            info("用户点击了停止自动回复按钮，开始关闭AI自动回复：")
            # 设置ai自动回复的标志位
            self.arisu_auto_reply_flag = False
            info("1.已设置AI自动回复的标志位为假")

            # 终止所有线程
            self.terminate_thread()
            info("2.已终止所有线程并销毁线程对象)")

            # 释放状态输出的窗口
            for groupBox in self.output_groupBox_list:  # 遍历容器列表(状态窗口的本质就是在容器里面)
                groupBox.deleteLater()   # 拿到第一个参数(窗口对象)，对窗口进行销毁，对象树机制会自动销毁里面的所有控件
            info("3.已销毁状态输出窗口的对象")
            # 清空列表
            self.thread_args_list.clear()           # 清空线程任务参数列表
            self.running_threads.clear()            # 清空放置线程对象列表
            self.output_groupBox_list.clear()       # 清空放置输出窗口容器的对象列表
            info("4.已清除线程任务参数列表、存储线程对象列表、存储窗口容器对象列表")
            info("已完成停止自动回复按钮所有逻辑")



        # 需要开启自动回复的情况
        elif self.SwitchReply.text() == "开启自动回复":
            # 判断是否开启了自动回复
            if not self.arisu_auto_reply_flag:  # 没有开启跳转就进行校验开启
                info("用户点击了开启自动回复按钮，检测到未开启AI自动回复，开始AI自动回复的逻辑代码")
                # 判断是否成功开启自动回复
                if self.create_state_monitor():  # 执行核心指令(AI自动回复)
                    # 按钮样式切换为关闭按钮（成功开启才改变按钮样式）
                    self.SwitchReply.setText("关闭自动回复")
                    self.SwitchReply.setStyleSheet("""
                                           QPushButton{border-radius: 10px;border-width:3px;border-color: rgb(255,0,0);
                                           border-style: solid;color: rgb(255,0,0);background-color: rgba(255,0,0,0.1);}
                                           QPushButton::hover{background-color: rgba(255,0,0,0.5);color: rgb(255, 255, 255);}
                                           QPushButton:pressed {background-color: rgb(255,0,0);color: rgb(255, 255, 255);}
                                               """)
            else:
                # 已经开启了自动回复直接跳转界面
                info("用户点击了开启AI自动回复按钮，但已开启了AI自动回复，自动跳转到监测界面")
                self.jump_state_output_widget()

        else:
            critical("牛逼，开启自动回复按钮字体被改了，源位置:\n")
            # print("牛逼，开启自动回复按钮字体被改了")

    def show_qq_group_info(self, current, previous):
        """QQ群列表选择项发生改变时显示Q群信息(currentItemChanged信号使用)
        current : 现在的选择项
        previous ： 上一个选择项
        """
        # prev_text = previous.text() if previous else "无"  # 防止无法访问导致卡死
        # curr_text = current.text() if current else "无"    # 防止无法访问导致卡死
        self.set_orign_tip()  # 输入框设置回正常的提示
        # 确保有选择项才读取显示
        if self.QQGroupList.currentRow() != -1:
            # 读取Q群的节和键值
            g_name = current.text()  # Q群名（也是节的名字）
            self.QQGroupName.setText(g_name)  # Q群名输入框
            self.BotName.setText(self.config.bind[g_name]["bot_name"])  # 机器人输入框
            self.Root.setText(self.config.bind[g_name]["root"])  # 最高权限者输入框
            self.ExitPassword.setText(self.config.bind[g_name]["exit_password"])  # 退出指令密码输入框
            self.InitRole.setText(self.config.bind[g_name]["init_role"])  # 初始人设输入框
            self.QQGroupLocation.setText(self.config.bind[g_name]["qq_group_location"])  # 窗口位置输入框
            if self.config.bind[g_name].getboolean("remove_dangerous_order"):  # 移除危险指令选择按钮
                self.RemoveDangerousOrder.setChecked(True)  # 设置为选中状态
            else:
                self.RemoveDangerousOrder.setChecked(False)  # 设置为未选中状态
        # 删除了所有选项
        else:
            self.QQGroupName.setText("")  # Q群名输入框
            self.BotName.setText("")  # 机器人输入框
            self.Root.setText("")  # 最高权限者输入框
            self.ExitPassword.setText("")  # 退出指令密码输入框
            self.InitRole.setText("")  # 初始人设输入框
            self.QQGroupLocation.setText("")  # 窗口位置输入框
            self.RemoveDangerousOrder.setChecked(False)  # 设置为未选中状态

    def show_qq_group_info2(self, event):
        """QQ群列表选择项发生改变时显示Q群信息(click信号使用)
        event : 事件
        """
        self.set_orign_tip()  # 输入框设置回正常的提示
        # 确保有选择项才读取显示(还有被选中的状态才读取)
        if self.QQGroupList.currentRow() != -1 and self.QQGroupList.selectedItems():
            # 读取Q群的节和键值
            g_name = self.QQGroupList.currentItem().text()  # Q群名（也是节的名字）
            self.QQGroupName.setText(g_name)  # Q群名输入框
            self.BotName.setText(self.config.bind[g_name]["bot_name"])  # 机器人输入框
            self.Root.setText(self.config.bind[g_name]["root"])  # 最高权限者输入框
            self.ExitPassword.setText(self.config.bind[g_name]["exit_password"])  # 退出指令密码输入框
            self.InitRole.setText(self.config.bind[g_name]["init_role"])  # 初始人设输入框
            self.QQGroupLocation.setText(self.config.bind[g_name]["qq_group_location"])  # 窗口位置输入框
            if self.config.bind[g_name].getboolean("remove_dangerous_order"):  # 移除危险指令选择按钮
                self.RemoveDangerousOrder.setChecked(True)  # 设置为选中状态
            else:
                self.RemoveDangerousOrder.setChecked(False)  # 设置为未选中状态
        # 删除了所有选项
        else:
            self.QQGroupName.setText("")  # Q群名输入框
            self.BotName.setText("")  # 机器人输入框
            self.Root.setText("")  # 最高权限者输入框
            self.ExitPassword.setText("")  # 退出指令密码输入框
            self.InitRole.setText("")  # 初始人设输入框
            self.QQGroupLocation.setText("")  # 窗口位置输入框
            self.RemoveDangerousOrder.setChecked(False)  # 设置为未选中状态

    def item_clicked(self):
        """同一个选择项被点击时，
        如果再次点击同一个选项且这个选项已经被选中就取消选中，
        如果再次点击同一个选项且这个选项已经没有被选中就选中这个选项
        """
        # # 如果点击原来的已经被选择的选择项才取消选择
        if self.previous_item == self.QQGroupList.currentItem() and self.QQGroupList.selectedItems():
            self.QQGroupList.clearSelection()  # 取消选中选择项
            self.previous_item = None  # 非常必要
        else:
            self.previous_item = self.QQGroupList.currentItem()  # 记录当前选择项

    """键盘快捷键"""
    def hotkey_github_doc(self):
        """热键跳转到Github和打开文档"""
        self.open_document()
        self.link_to_github()

    def hotkey_dynamic_background_create(self):
        """热键动态背景生成"""
        # 判断是否已经存在,避免重复创建
        if self.video_player is None:
            self.video_player = QMediaPlayer(self)  # 创建多媒体播放器
            self.video_player.setVideoOutput(self.DynamicBackground)  # 多媒体播放器设置窗口来视频输出
            self.video_player.setSource(QUrl("qrc:/背景/背景/动态视频.mp4"))  # 设置播放资源，fromLocalFile处理路径问题
            self.DynamicBackground.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatioByExpanding)  # 保持宽高比并填充整个控件
            self.video_player.setLoops(QMediaPlayer.Loops.Infinite)  # 循环无限次数
            self.video_player.play()  # 开始播放
            info("动态背景生成热键：动态背景已重新生成")
        else:
            info("动态背景生成热键：动态背景已存在，不需要重新生成")

    def hotkey_dynamic_background_del(self):
        """热键动态背景删除"""
        # 判断是否已经存在,避免重复输出
        if self.video_player is not None:
            self.video_player.stop()        # 停止视频播放
            self.video_player = None        # 重新造一个空的属性（后续可能需要重新创建回来）
            self.DynamicBackground.update()  # 强制刷新控件（可能清空画面）
            info("动态背景删除热键：动态背景已成功删除")
        else:
            info("动态背景删除热键：动态背景已经被删除，过滤重复删除")

    def hotkey_switch_full_screen(self):
        """打开/关闭全屏"""
        # 判断是否是全屏状态
        if self.isFullScreen():
            self.showNormal()   # 恢复正常
            info("成功恢复窗正常状态")
        else:
            self.showFullScreen()   # 全屏
            info("成功打开全屏功能")

    # 开发者功能
    def console_widget_visible(self):
        """显示或隐藏输入输出重定向窗口"""
        # 判断是否已经隐藏
        if self.ConsoleWidget.isHidden():
            self.SettingsScrollArea.hide()  # 隐藏设置滚动控件
            self.ConsoleWidget.show()       # 显示输入输出重定向窗口
            self.jump_settings_widget()     # 跳转到用户设置界面
            # self.setStyleSheet("background-color: rgb(128, 128, 128);")  # 切换整个窗口的样式
            info("已打开输入输出重定向窗口并跳转到该窗口")
        else:
            self.SettingsScrollArea.show()  # 显示设置滚动控件
            self.ConsoleWidget.hide()       # 隐藏输入输出重定向窗口
            # self.setStyleSheet("background-color: rgb(240, 244, 249);") # 切换整个窗口的样式
            info("已隐藏输入输出重定向窗口")
        # self.ConsoleWidget.clearFocus()  # 清除焦点

    @staticmethod
    def open_cmd():
        """打开一个cmd窗口"""
        os.system("start cmd")  # 打开新窗口并立即返回控制
        info("已打开一个cmd窗口")

    """用户设置"""
    def jump_settings_widget(self):
        """跳转到用户设置界面"""
        # 跳转到用户设置界面（设置当前选项卡的界面，从配置文件里面拿到数据，需要类型转换）
        self.ModeWidget.setCurrentIndex(int(self.config.user_settings["用户界面位置"]["用户设置"]))
        return False

    def restore_navigation_bar_sorting(self):
        """还原导航栏排序"""
        location = self.config.original_interface_location()  # 从配置文件里面拿到初始位置
        tab_widget = [self.ModeWidget.widget(index) for index in range(self.ModeWidget.count())]  # 读取标签页的所有界面
        for widget in tab_widget:
            # 找到当前遍历标签页的下标->从配置文件的字典中找到原来的下标->根据当前的下表移动到最开始位置的下标
            self.tab_bar.moveTab(self.ModeWidget.indexOf(widget), int(location[widget.objectName()]))

    def initial_interface_location_selector(self):
        """初始界面位置选择"""
        self.config.user_settings["初始界面位置"]["init_index"] = str(
            self.InitialInterfaceLocationComboBox.currentIndex())  # 设置初始界面的位置
        # print(self.InitialInterfaceLocationComboBox.currentIndex())
        self.config.save_user_settings_ini()  # 更新用户设置ini配置写入硬盘中

    def tip_api_key_exist(self):
        """提示用户密钥是否存在"""
        if keyring.get_password("DEEPSEEK_API_KEY", "爱丽丝") and self.APIKeyInput.text() == "":
            # 检验密钥是否还有效（可能录入后销毁了）
            try:
                # 测试请求到模型列表端点
                response = requests.get(
                    "https://api.deepseek.com/user/balance",  # 请求网址
                    # 请求头(从密钥仓库里面拿到key)
                    headers={"Authorization": f"Bearer {keyring.get_password("DEEPSEEK_API_KEY", "爱丽丝")}"},
                    timeout=5  # 添加超时设置，防止卡死
                )
                if response.status_code != 200:  # 检查响应状态码
                    self.APIKeyState.setStyleSheet("color: red;border: none;")  # 样式表设置字体为红色并且为无边框
                    self.APIKeyState.setTitle("密钥失效")
                    # print("存储的密钥失效了")
                    warning("存储的密钥失效了")
                    return False
                else:
                    self.APIKeyState.setStyleSheet("color: green;border: none;")  # 样式表设置字体为红色并且为无边框
                    self.APIKeyState.setTitle("密钥有效")
                    info("检测到存储的密钥有效")
                    return True
            except requests.exceptions.RequestException:  # 捕获所有网络相关异常
                # print(f"初始化无法检测密钥有效，网络问题\n{e}")  # 打印输出异常
                # warning(f"初始化无法检测密钥有效，网络问题\n{e}")
                exception("初始化无法检测密钥有效，错误信息:\n")
                self.APIKeyState.setStyleSheet("color: red;border: none;")  # 样式表设置字体为红色并且为无边框
                self.APIKeyState.setTitle("连接超时")
                return False
        else:
            self.APIKeyState.setStyleSheet("color: red;border: none;")  # 样式表设置字体为红色并且为无边框
            self.APIKeyState.setTitle("没有密钥")
            # print("界面初始化时没有找到密钥")
            warning("界面初始化时没有找到密钥")  # 等到启动进程池时发现没有密钥而崩溃才用更高级的日志方法
        return False

    def __api_key_confirm(self):
        """检测api有效和把deepseek注入到系统变量（出于安全考虑使用私有方法）
        1. 检查密钥是否已经存在功能 2. 检测api是否有效。 1. 把有效的api写入用户环境变量
        """
        # 检查密钥是否已经录入
        if keyring.get_password("DEEPSEEK_API_KEY", "爱丽丝") and self.APIKeyInput.text() == "":
            self.APIKeyState.setStyleSheet("color: green;border: none;")  # 样式表设置字体为绿色并且为无边框
            self.APIKeyState.setTitle("存在密钥")
            info("点击确定按钮启用检测功能，检测到密钥已经存在")
            return True  # 不往下执行直接退出
        # 初次密钥录入
        try:
            # 测试请求到模型列表端点
            response = requests.get(
                "https://api.deepseek.com/user/balance",  # 请求网址
                headers={"Authorization": f"Bearer {self.APIKeyInput.text()}"},  # 请求头(从文本控件里面拿到key)
                timeout=5  # 添加超时设置，防止卡死
            )
            if response.status_code != 200:  # 检查响应状态码
                self.APIKeyState.setStyleSheet("color: red;border: none;")  # 样式表设置字体为红色并且为无边框
                self.APIKeyState.setTitle("密钥无效")  # 展示字体在QGroupBox上
                # print("输入的API密钥无效或未授权")
                warning("输入的API密钥无效或未授权")
            else:
                self.APIKeyState.setStyleSheet("color: green;border: none;")  # 样式表设置字体为绿色并且为无边框
                self.APIKeyState.setTitle("密钥有效")
                info("密钥有效")
                # 存储密钥
                keyring.set_password("DEEPSEEK_API_KEY", "爱丽丝", self.APIKeyInput.text())
                # print("API密钥有效，已将密钥存储完毕")
                info("API密钥有效，已将密钥存储完毕")
        except requests.exceptions.RequestException:  # 捕获所有网络相关异常
            # print(e)  # 打印输出异常
            exception("网络请求失败，错误信息:")  # 打印输出异常并记录异常
            self.APIKeyState.setStyleSheet("color: red;border: none;")  # 样式表设置字体为红色并且为无边框
            self.APIKeyState.setTitle("连接超时")
            return False
        return True

    def tip_logic_cpu_count(self):
        """提示用户可以使用的逻辑CPU数量，并自动计算最合适的CPU数量"""
        if platform.processor():
            info(f"真实cpu的名字:{platform.processor()}")
        else:
            warning(f"真实CPU的名字未知")
        if psutil.cpu_count(False) and psutil.cpu_count(True):  # 能获取到CPU核心数才执行最佳计算
            physical_cores = psutil.cpu_count(False)  # 物理核心数
            logical_cores = psutil.cpu_count(True)  # 逻辑核心数
            use_cores = min(int(physical_cores * 1.5), logical_cores)  # 使用核心数
            self.LogicCPUCount.setText(f"{use_cores}")
            self.LogicCPUCountState.setStyleSheet("color: green;border: none;")  # 提示样式表设置字体为绿色并且为无边框
            self.LogicCPUCountState.setTitle(f"最大可使用核心{logical_cores},使用最大时建议-2(留给系统)")
            info(f"物理核心数:{physical_cores},逻辑核心数:{logical_cores},进程池使用的核心数:{use_cores}")
        else:
            self.LogicCPUCount.setText("4")
            self.LogicCPUCountState.setStyleSheet("color: red;border: none;")  # 提示样式表设置字体为红色并且为无边框
            self.LogicCPUCountState.setTitle("无法计算核心数,已使用默认值4")
            critical("无法获取系统的物理核心数或逻辑核心数进行计算，将改为使用4逻辑核心")

    def logic_cup_confirm(self):
        """逻辑cup按钮确认"""
        # 能够拿到逻辑核心数的情况
        if psutil.cpu_count(True):  # 判断逻辑核心数是否有值
            logical_cores = psutil.cpu_count(True)  # 逻辑核心数
            try:
                default_core = int(self.LogicCPUCount.text())  # 接收用户输入的核心数
            except ValueError:
                self.LogicCPUCount.setText(str(logical_cores - 2))  # 自动修正
                warning(
                    f"使用逻辑核心数输入错误，用户输入值：{self.LogicCPUCount.text()}。自动修正为最大逻辑核心数{logical_cores - 2}")
                self.LogicCPUCountState.setStyleSheet("color: red;border: none;")  # 提示样式表设置字体为红色并且为无边框
                self.LogicCPUCountState.setTitle(f"输入错误，已修正")
                return True  # 这里执行完毕不往后执行了
            # 判断是否过大或过小
            if default_core < 0:  # 输入一个负数值
                self.LogicCPUCount.setText("1")  # 自动修正
                warning(f"使用逻辑核心数输入错误，用户输入值：{self.LogicCPUCount.text()}。自动修正为1逻辑核心数")
                self.LogicCPUCountState.setStyleSheet("color: red;border: none;")  # 提示样式表设置字体为红色并且为无边框
                self.LogicCPUCountState.setTitle(f"超出逻辑核心最大值，已修正")
            if default_core > logical_cores:  # 如果用户输入的核心数比逻辑核心数大则使用最大的逻辑核心数
                self.LogicCPUCount.setText(str(logical_cores))  # 自动修正
                warning(f"用户输入逻辑核心数超过最大值{logical_cores}，自动修正为最大逻辑核心数{logical_cores}")
                self.LogicCPUCountState.setStyleSheet("color: red;border: none;")  # 提示样式表设置字体为红色并且为无边框
                self.LogicCPUCountState.setTitle(f"超出核心最小值，已修正")
            else:
                self.LogicCPUCount.setText(str(default_core))  # 录入修改
                info(f"成功修改使用的逻辑核心数:{self.LogicCPUCount.text()}")
                self.LogicCPUCountState.setStyleSheet("color: green;border: none;")  # 提示样式表设置字体为绿色并且为无边框
                self.LogicCPUCountState.setTitle(f"修改成功")
        # 无法获取用户的逻辑核心数
        else:
            warning("无法检测用户的最大逻辑核心数，用户输入的最大值将无法控制")
            try:
                default_core = int(self.LogicCPUCount.text())  # 接收用户输入的核心数
            except ValueError:
                warning(f"使用逻辑核心数输入错误，用户输入值：{self.LogicCPUCount.text()}。自动修正为最大逻辑核心数1")
                self.LogicCPUCountState.setStyleSheet("color: red;border: none;")  # 提示样式表设置字体为红色并且为无边框
                self.LogicCPUCountState.setTitle(f"输入错误，已修正")
                return True  # 这里执行完毕不往后执行了
            if default_core < 0:  # 输入一个负数值
                self.LogicCPUCount.setText("1")  # 自动修正
                warning(f"使用逻辑核心数输入错误，用户输入值：{self.LogicCPUCount.text()}。自动修正为1逻辑核心数")
                self.LogicCPUCountState.setStyleSheet("color: red;border: none;")  # 提示样式表设置字体为红色并且为无边框
                self.LogicCPUCountState.setTitle(f"超出逻辑核心最大值，已修正")
            else:
                self.LogicCPUCount.setText(str(default_core))  # 录入修改
                info(f"成功修改使用的逻辑核心数:{self.LogicCPUCount.text()}")
                self.LogicCPUCountState.setStyleSheet("color: green;border: none;")  # 提示样式表设置字体为绿色并且为无边框
                self.LogicCPUCountState.setTitle(f"修改成功")
        return True

    def open_role_repository_directory(self):
        """打开人设库目录"""
        # 判断文件是否存在和打开文档
        try:
            if os.path.exists(r".\用户设置\提示库"):  # 实际开发路径
                os.startfile(r".\用户设置\提示库")  # 打开文档，注意路径符号
                info("使用开发路径后文档打开了")
            elif os.path.exists(r"..\用户设置\提示库"):  # 当前测试路径
                os.startfile(r"..\用户设置\提示库")  # 打开文档，注意路径符号
                info("使用测试路径后文档打开了")
            else:
                exception("提示库文件夹不存在")
                print("提示库文件夹不存在")
                # 错误弹窗提示
                QMessageBox.critical(self, "错误提示", "提示库文件夹不存在", QMessageBox.StandardButton.Ok,
                                     QMessageBox.StandardButton.Ok)
                warning("提示库文件夹不存在，可能被删除了")
        # 异常处理
        except Exception as e:
            # print(f"打开文档失败: {str(e)}")  # 输出错误信息
            QMessageBox.critical(self, "错误提示", str(e), QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.Ok)
            exception("提示库文件夹不存在")
            print("提示库文件夹不存在")

    def open_keyword_reply_directory(self):
        """打开关键词回复目录"""
        # 判断文件是否存在和打开文档
        try:
            if os.path.exists(r".\用户设置\关键词回复"):  # 实际开发路径
                os.startfile(r".\用户设置\关键词回复")  # 打开文档，注意路径符号
                info("使用开发路径后文档打开了")
            elif os.path.exists(r"..\用户设置\关键词回复"):  # 当前测试路径
                os.startfile(r"..\用户设置\关键词回复")  # 打开文档，注意路径符号
                info("使用测试路径后文档打开了")
            else:
                exception("关键词回复文件夹不存在")
                print("关键词回复文件夹不存在")
                # 错误弹窗提示
                QMessageBox.critical(self, "错误提示", "关键词回复文件夹不存在", QMessageBox.StandardButton.Ok,
                                     QMessageBox.StandardButton.Ok)
                warning("关键词回复文件夹不存在，可能被删除了")
        # 异常处理
        except Exception as e:
            # print(f"打开文档失败: {str(e)}")  # 输出错误信息
            QMessageBox.critical(self, "错误提示", str(e), QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.Ok)
            exception("关键词回复文件夹不存在")
            print("关键词回复文件夹不存在")

    def open_jm_strategy_file(self):
        """打开禁漫天堂的策略文件"""
        # 判断文件是否存在和打开文档
        try:
            if os.path.exists(r".\用户设置\option.yml"):  # 实际开发路径
                os.startfile(r".\用户设置\option.yml")  # 打开文档，注意路径符号
                info("使用开发路径后文档打开了")
            elif os.path.exists(r"..\用户设置\option.yml"):  # 当前测试路径
                os.startfile(r"..\用户设置\option.yml")  # 打开文档，注意路径符号
                info("使用测试路径后文档打开了")
            else:
                exception("禁漫天堂的策略文件不存在")
                print("禁漫天堂的策略文件不存在")
                # 错误弹窗提示
                QMessageBox.critical(self, "错误提示", "禁漫天堂的策略文件不存在", QMessageBox.StandardButton.Ok,
                                     QMessageBox.StandardButton.Ok)
                warning("禁漫天堂的策略文件不存在，可能被删除了")
        # 异常处理
        except Exception as e:
            # print(f"打开文档失败: {str(e)}")  # 输出错误信息
            QMessageBox.critical(self, "错误提示", str(e), QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.Ok)
            exception("禁漫天堂的策略文件不存在")
            print("禁漫天堂的策略文件不存在")

    def open_log_directory(self):
        """打开日志目录"""
        # 判断文件是否存在和打开文档
        try:
            if os.path.exists(r".\logs"):  # 实际开发路径
                os.startfile(r".\logs")  # 打开文档，注意路径符号
                info("使用开发路径后文档打开了")
            elif os.path.exists(r"..\logs"):  # 当前测试路径
                os.startfile(r"..\logs")  # 打开文档，注意路径符号
                info("使用测试路径后文档打开了")
            else:
                exception("日志目录不存在")
                print("日志目录")
                # 错误弹窗提示
                QMessageBox.critical(self, "错误提示", "日志目录不存在", QMessageBox.StandardButton.Ok,
                                     QMessageBox.StandardButton.Ok)
                warning("日志目录不存在，可能被删除了")
        # 异常处理
        except Exception as e:
            # print(f"打开文档失败: {str(e)}")  # 输出错误信息
            QMessageBox.critical(self, "错误提示", str(e), QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.Ok)
            exception("日志目录不存在")
            print("日志目录不存在")

    def uninstall(self):
        """卸载操作（回收资源卸载软件本体和软件产生的文件）"""
        # 回收密钥(需要先判断密钥是否存在)
        if keyring.get_password("DEEPSEEK_API_KEY", "爱丽丝"):
            keyring.delete_password("DEEPSEEK_API_KEY", "爱丽丝")
            # print("已从系统密钥库删除密钥")
            info("已从系统密钥库删除密钥")
        else:
            # print("密钥不存在，无需删除")
            info("密钥不存在，无需删除")
        # 回收在temp目录下的视频资源
        self.video_player.deleteLater()  # 删除视频播放对象
        # 延迟删除残留在temp文件的MP4动态壁纸文件（确保资源完全释放才删除）
        QTimer.singleShot(1000, clear_temp)  # 延迟1秒
        self.Uninstall.setText("施工中...")
        # 剩下的之后写
        pass

    """检查用户输入合法性的相关方法"""

    def check_role_exist(self, role_name):
        """判断人设是否存在提示库
        role_name : 人设名称
        """
        if not role_name:  # 人设为空
            self.InitRole.setText("爱丽丝")  # 设置为默认人设
            return True
        elif os.path.isfile(f"./用户设置/提示库/{role_name}.txt") or os.path.isfile(
                f"../用户设置/提示库/{role_name}.txt"):
            return True
        self.InitRole.setPlaceholderText("人设不存在")  # 提示用户是否存在人设
        self.InitRole.setText("")  # 设置为空让用户重输
        return False  # 条件都不符合直接放回False

    def check_qq_group_location_input(self, string):
        """判断窗口坐标输入是否有效
        string ： 窗口坐标字符串
        """
        # 字符串为空
        if not string:
            self.QQGroupLocation.setText("0,0")  # 设置为0,0
            return True  # 返回默认参数
        # 1.判断是否有逗号 2.替换统一逗号后分割字符串进行类型转换
        # 检查是否有，或,
        elif ',' in string or '，' in string:
            # 替换完后转换类型看是否满足可以转为整型
            location = string.replace("，", ",").split(",", 1)
            try:
                _, _ = int(location[0]), int(location[1])
            except ValueError:
                self.QQGroupLocation.setPlaceholderText("坐标输入错误")
                self.QQGroupLocation.setText("")  # 设置为空让用户重输
                return False
            return True  # 符合要求
        # 输入错误的情况
        else:
            self.QQGroupLocation.setPlaceholderText("坐标输入错误")
            self.QQGroupLocation.setText("")  # 设置为空让用户重输
        return False

    def set_orign_tip(self):
        """设置回原来的tip（点击添加或修改按钮后如果有错会修改tip，使用这个切回来）"""
        self.QQGroupName.setPlaceholderText("请输入Q群名(优先备注名)")
        self.BotName.setPlaceholderText("机器人名字(优先群内备注名)")
        self.Root.setPlaceholderText("最高权限者(只能有一个)")
        self.ExitPassword.setPlaceholderText("退出指令的密码(不能为空)")
        self.InitRole.setPlaceholderText("初始人设(不填默认爱丽丝)")
        self.QQGroupLocation.setPlaceholderText("Q群窗口的位置(不填默认0,0)")

    """重写事件"""

    def closeEvent(self, event):
        sys.stderr = None  # 错误输出重定向为空(之前进行重定向了)
        sys.stdout = None  # 输出重定向为空(之前进行重定向了)
        self.terminate_thread()  # 停止所有正在运行的线程
        clear_temp()  # 删奇怪溢出的视频缓存
        super().closeEvent(event)  # 继承之前的关闭功能

    def keyPressEvent(self, event):
        # 先继承父类的方法
        super().keyPressEvent(event)
        # if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
        #     # 执行回车键或返回键的处理逻辑
        #     print(event.text())
        # print(event.text())

    """后端核心功能"""

    def create_state_monitor(self):
        """创建状态监视器
        根据绑定文件添加，被Home的按钮和自动开启回复所连接信号
        返回值：
        如果成功开启返回True,否则返回False
        """
        """校验是否有开启的资格"""
        info("开始进行校验，检查是否拥有开启AI自动回复的资格：")
        # 用户没有任何绑定群聊的情况
        if len(self.config.bind.sections()) == 0:
            self.jump_bind_widget()  # 跳转到绑定界面
            critical("用户没有任何绑定配置，不开启AI自动回复功能，自动跳转到Q群绑定界面")
            QMessageBox.critical(self, "错误提示", "请先进行Q群绑定配置（记得登陆QQ后把需要绑定Q聊窗口单独打开），不会就看文档问人。"
                                                   "就在这个界面填写好信息点击添加就算是绑定成功了。",
                                 QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
            return False
        else:
            info("1.绑定配置检测通过(已经有绑定的群聊)")
        # 密钥无效的情况
        if not self.check_api_key():  # 调用检查密钥的方法
            critical("未通过密钥有效性检测")
            return False
        else:
            info("2.密钥检测配置通过")

        # 检测通过，有资格开启AI回复功能
        if self.jump_state_output_widget():
            info("所有检测通过，满足开启AI自动的资格，已自动跳转到状态输出界面")
        else:
            critical("所有检测通过，满足开启AI自动的资格，但是未自动跳转到状态输出界面，界面可能遭到篡改")

        """创建状态监听窗口和进程池创建"""
        # 拿到绑定ini的所有节
        for section in self.config.bind.sections():
            # 拿到绑定窗口的信息用来创建状态监视窗口
            args = self.config.get_bind_keys(section)
            # 创建监视器窗口并添加状态监视器窗口到监测选项卡
            output_widget = self.add_state_monitor(args[0], args[1], args[2], args[3], args[4], args[5], args[6])
            # 把创建的窗口对象(QGroupBox容器)放进列表里方便统一销毁[直接删除父容器（QGroupBox）是最简单且最安全的做法)]
            self.output_groupBox_list.append(output_widget[0])
            # 把创建的对象添加到进程参数列表里面去
            self.thread_args_list.append((output_widget[1], args[0], args[1], args[2], args[3], args[4], args[5], args[6]))

        info(f"所有状态监听窗口已创建完成，共创建了{len(self.config.bind.sections())}个窗口")
        """进程池创建和绑定"""
        # 设置线程池核心数
        self.thread_pool.setMaxThreadCount(int(self.LogicCPUCount.text()))
        # Qt线程池任务构建
        for args in self.thread_args_list:  # 遍历参数
            # 传入参数创建线程
            arisu_threading = ArisuThreading(args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7])
            # 连接线程信号到QTextBrowser（GUI更新）
            arisu_threading.signal.print_signal.connect(self.print_signal)      # 状态输出
            arisu_threading.signal.error_signal.connect(self.restart_thread)    # 崩溃处理
            # 设置任务完成（或崩溃）后自动删除该线程对象
            arisu_threading.setAutoDelete(True)
            # 添加线程到列表
            self.running_threads.append(arisu_threading)
            # 传入县城里池并开始线程
            self.thread_pool.start(arisu_threading)

            # 日志输出提示
            info(f"成功创建 {args[1]} 窗口的控制线程")

        # 打开自动回复的标志
        self.arisu_auto_reply_flag = True
        return True

    @staticmethod
    @pyqtSlot(QTextBrowser, str)
    def print_signal(text_browser : QTextBrowser, text : str):
        """被连接的信号（监控输出窗口的更新）
        参数：
        text_browser ： QTextBrowser对象
        text ： 更新的文本
        """
        # 添加文本到控件中
        text_browser.append(text)

    @pyqtSlot(QTextBrowser, ArisuThreading, str)
    def restart_thread(self, text_browser : QTextBrowser, crash_object : ArisuThreading, crash_msg : str):
        """重启线程
        回调参数：
        text_browser ： QTextBrowser对象,用来输出
        crash_object ： 崩溃对象
        crash_msg ： 崩溃信息
        """
        # 崩溃信息直接发到状态列表里面去
        text_browser.append(crash_msg)
        warning(f"检测到线程池里面的线程崩溃,失去对 {crash_object.qq_group_name} 窗口的控制，将在10秒后重启该线程")
        # 线程重启
        def restart():
            """线程重启
            1.不需要对已经构建好的窗口控件重开，只需要重开线程就好了
            2.需要清理掉之前保存的线程对象，因为线程对象实际已经死亡
            """
            # 遍历正在运行的线程对象，并把死去的线程对象给移除
            for index, thread_object in enumerate(self.running_threads):
                # 找出正在运行的线程对象列表崩溃的线程对象
                if crash_object is thread_object:
                    # 拿到崩溃线程的任务参数
                    args = self.thread_args_list[index]
                    # 传入参数重新创建这个崩溃的线程
                    arisu_threading = ArisuThreading(args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7])
                    # 连接线程信号到QTextBrowser（GUI更新）
                    arisu_threading.signal.print_signal.connect(self.print_signal)  # 状态输出
                    arisu_threading.signal.error_signal.connect(self.restart_thread)  # 崩溃处理
                    # 设置任务完成（或崩溃）后自动删除该线程对象
                    arisu_threading.setAutoDelete(True)
                    # 用新的线程替换已经死亡的线程
                    self.running_threads[index] = arisu_threading
                    # 传入线程池并重新开始线程
                    self.thread_pool.start(arisu_threading)
                    # 跳出遍历
                    break
            else:
                critical("卧槽，有挂！没有在self.running_threads里找到对应的崩溃线程对象，只能是数据被篡改了吧？")

        # 延迟10秒才进程重启
        QTimer.singleShot(10000, restart)


    def terminate_thread(self):
        """终止线程"""
        # 取消所有排队任务
        self.thread_pool.clear()
        # 设置超时
        self.thread_pool.waitForDone(100)
        # 遍历正在运行的线程
        for thread in self.running_threads:
            thread.disconnect_signal()  # 断开信号连接
            thread.is_task_progress = False  # 设置标志位为假

    def check_api_key(self):
        """检查api是否存在以及是否有效
        返回值：
        存在密钥且有效返回True，无效返回False并展示提示错误窗口
        """
        # 密钥不存在
        if not keyring.get_password("DEEPSEEK_API_KEY", "爱丽丝"):
            QMessageBox.critical(self, "错误提示", "请先配置deepseek的api密钥，不会的看文档、看视频、问AI、问别人",
                                 QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
            return False
        # 密钥存在
        else:
            # 检查密钥是否有效
            try:
                # 测试请求到模型列表端点
                response = requests.get(
                    "https://api.deepseek.com/user/balance",  # 请求网址
                    headers={"Authorization": f"Bearer {keyring.get_password("DEEPSEEK_API_KEY", "爱丽丝")}"},
                    # 请求头(从文本控件里面拿到key)
                    timeout=5  # 添加超时设置，防止卡死
                )
                if response.status_code != 200:  # 检查响应状态码
                    QMessageBox.critical(self, "错误提示", "之前配置的密钥已无效，请重新配置",
                                         QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
                    return False
            except requests.exceptions.RequestException as e:  # 捕获所有网络相关异常
                QMessageBox.critical(self, "错误提示", f"连接超时，请重新试或重接网络。错误代码：{str(e)}",
                                     QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
                exception("检查api是否存在及有效的方法。网络请求失败，错误信息:")  # 打印输出异常并记录异常
                return False
        return True  # 响应状态码等于200


# def arisu_ai_auto_reply_task(print_widget: QTextBrowser, qq_group_name: str, bot_name: str, root: str,
#                              exit_password: str, init_role: str,
#                              qq_group_location: str, remove_dangerous_order: str):
#     """爱丽丝AI自动回复任务
#     is_task_progress ： 任务完成标志位（内存共享变量）
#     qq_group_name ：QQ群名
#     bot_name ：机器人名
#     root ：最高权限者
#     exit_password ：退出指令的密码
#     init_role ：初始人设
#     qq_group_location ：0,0（窗口的位置，文本的形式）
#     remove_dangerous_order ：False（布尔值）
#     """
#     """输出重定向"""
#     # sys.stdout = OutputRedirection()  # 实例化输出重定向
#     # sys.stdout.text_print.connect(print_widget.append)  # 传入输出窗口并打通信号
#     # print("\033[91m测试完成\033[0m")
#     """实例化对象"""
#     # print(qq_group_name, bot_name, root, exit_password, init_role, qq_group_location, remove_dangerous_order)
#     # deepseek消息回复(示例化对象没有顺序要求)
#     deepseek = DeepseekConversationEngine(init_role)  # 给deepseek这个外部变量赋值（让外部函数也能调用）
#
#     # qq消息监听者
#     arisu = QQMessageMonitor(qq_group_name, bot_name, 4)
#
#     # 外部函数(传入需要的对象)
#     ef = ArisuQQChatAICore(deepseek, arisu, root, exit_password, qq_group_location, remove_dangerous_order)
#
#     # 保持窗口(显示、位置、大小)，设置10秒进行一次保持
#     # ef.thread_keep_win(sleep_time := 10)  # 我用个海象不过分
#     # print(f"窗口位置:{ef.qq_group_x, ef.qq_group_y}\t保持原始窗口的刷新时间:{sleep_time}秒/刷")
#     """核心循环逻辑"""
#     # while is_task_progress.value:  # 使用.value访问共享变量的值:
#     while True:
#         """监听窗口控制"""
#         # 一秒监听一次窗口，防止CUP占用过高
#         sleep(1)
#         arisu.monitor_message()  # 始监控
#         """消息处理"""
#         if len(arisu.message_processing_queues) > 0:  # 消息队列不为空，进行队列处理
#             reply = ef.split_respond_msg()  # 解析需要回应的消息
#             arisu.message_processing_queues.pop(0)  # 清理回应的消息(出队)[必须在split_respond_msg之后]
#             """开始消息处理逻辑（不是聊天就是指令）"""
#             # 非指令
#             if not reply[3]:
#                 """聊天回复"""
#                 reply = deepseek.ask(f"{reply[0]}:{reply[1]}，时间:{reply[2]}", False)  # 发出请求并回应(这里不重复打印到屏幕上)
#                 arisu.send_message(reply)
#             # 接收到了指令（检测指令是否存在）
#             elif ef.is_order(reply[1]):  # 指令库里面检索指令(顺序不能反，因为指令可能带有参数)
#                 """指令操作"""
#                 # 分割指令和参数
#                 order, args = ef.split_order_args(reply[1])
#                 # 是否有权限调度指令(包括root和非root的指令)
#                 if ef.check_permission(order, reply[0]):  # 传入指令和发送者
#                     arisu.send_message(ef.execute_order(order, args))  # 传入指令执行后拿到返回结果并发送
#                 else:
#                     arisu.send_message("雑魚权限？真の杂鱼~🐟呢")  # 传入指令执行后拿到返回结果并发送
#             else:
#                 """使用了不存在的指令(不是聊天也无法调用指令库的指令)"""
#                 print("接收到了一条不存在的指令(不是聊天也没有在指令库中找到指令)")
#                 arisu.send_message("不存在该指令")
#         else:
#             pass  # print("出现新消息，这里不进行打印，因为监视方法已经打印了")

if __name__ == "__main__":
    app = QApplication(sys.argv)  # 管理控制事件流和设置(sys.argv控制台接收参数)
    window = (

        ArisuUI("爱丽丝", True, "../resources/Arisu.ui"))
    window.show()
    sys.exit(app.exec())  # 安全退出界面任务
