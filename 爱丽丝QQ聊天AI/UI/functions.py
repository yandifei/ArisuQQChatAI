"""非UI功能实现
前后端分离，ExtendUI.py从这里导入非UI的功能函数
"""
# 系统库
import os   # 系统库
import re   # 正则库
# 第三方库
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QProcess
# 自己的库
from arisu_logger import debug, info, warning, critical, exception                     # 导入日志方法

class OutputRedirection(QObject):
    """输入重定向"""
    text_print = pyqtSignal(str)   # 打造输出信号(必须放最高层级)
        # console_handler.stream = self   # 输出重定向为自己

    def write(self, text):
        # self.text_print.emit(text)
        self.text_print.emit(self.remove_ansi_escape(text))


    @staticmethod
    def remove_ansi_escape(text):
        """移除ANSI转义序列"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    #
    # # def convert_ansi_to_html(self, text):
    # #     """将ANSI转义序列转换为HTML标签"""
    # #     # 处理ANSI序列的正则表达式
    # #     ansi_pattern = re.compile(r'\033\[([\d;]*)m')
    #
    #
    # # 颜色映射(ANSI 颜色到 HTML 颜色的映射)
    # color_map = {
    #     '30': 'black',  # 黑色
    #     '31': 'red',  # 红色
    #     '32': 'green',  # 绿色
    #     '33': 'yellow',  # 黄色
    #     '34': 'blue',  # 蓝色
    #     '35': 'magenta',  # 洋红
    #     '36': 'cyan',  # 青色
    #     '37': 'white',  # 白色
    #     '90': 'gray',  # 亮黑（灰色）
    #     '91': '#FF5555',  # 亮红色
    #     '92': '#55FF55',  # 亮绿色
    #     '93': '#FFFF55',  # 亮黄色
    #     '94': '#5555FF',  # 亮蓝色
    #     '95': '#FF55FF',  # 亮洋红
    #     '96': '#55FFFF',  # 亮青色
    #     '97': '#FFFFFF',  # 亮白色
    #     '0': ''  # 重置
    # }

# class ArisuProcessPool(QProcess):
#     # 定义信号：传递任务结果、错误和进度
#     result = pyqtSignal(object)
#     error = pyqtSignal(str)
#     progress = pyqtSignal(int)
#
#     def __init__(self, cpu_cores : int, process_args_list, is_task_progress, qq_group_name, bot_name, root, exit_password,
#                  init_role, qq_group_location, remove_dangerous_order):
#         super().__init__()
#         """Qt进程
#         cpu_cores ： 进程池核心数量
#         process_args_list ： 任务参数列表
#         爱丽丝AI自动回复任务
#         is_task_progress ： 任务完成标志位（内存共享变量）
#         qq_group_name ：QQ群名
#         bot_name ：机器人名
#         root ：最高权限者
#         exit_password ：退出指令的密码
#         init_role ：初始人设
#         qq_group_location ：0,0（窗口的位置，文本的形式）
#         remove_dangerous_order ：False（布尔值）
#         """
#         self.cpu_cores = cpu_cores
#         self.process_args_list = process_args_list # 进程参数列表
#         self.pool = None
#         self.running = True   # 结束进程池信号
#         # 属性
#         self.is_task_progress = is_task_progress
#         self.qq_group_name = qq_group_name
#         self.bot_name = bot_name
#         self.root = root
#         self.exit_password = exit_password
#         self.init_role = init_role
#         self.qq_group_location = qq_group_location
#         self.remove_dangerous_order= remove_dangerous_order
#
#     def run(self):
#
#         """输出重定向"""
#         # sys.stdout = OutputRedirection()  # 实例化输出重定向
#         # sys.stdout.text_print.connect(print_widget.append)  # 传入输出窗口并打通信号
#         # print("\033[91m测试完成\033[0m")
#         """实例化对象"""
#         # print(qq_group_name, bot_name, root, exit_password, init_role, qq_group_location, remove_dangerous_order)
#         # deepseek消息回复(示例化对象没有顺序要求)
#         deepseek = DeepseekConversationEngine(self.init_role)  # 给deepseek这个外部变量赋值（让外部函数也能调用）
#
#         # qq消息监听者
#         arisu = QQMessageMonitor(self.qq_group_name, self.bot_name, 4)
#
#         # 外部函数(传入需要的对象)
#         ef = ArisuQQChatAICore(deepseek, arisu, self.root, self.exit_password, self.qq_group_location, self.remove_dangerous_order)
#
#         # 保持窗口(显示、位置、大小)，设置10秒进行一次保持
#         ef.thread_keep_win(sleep_time := 10)  # 我用个海象不过分
#         print(f"窗口位置:{ef.qq_group_x, ef.qq_group_y}\t保持原始窗口的刷新时间:{sleep_time}秒/刷")
#         """核心循环逻辑"""
#         # while is_task_progress.value:  # 使用.value访问共享变量的值:
#         while True:
#             """监听窗口控制"""
#             # 一秒监听一次窗口，防止CUP占用过高
#             sleep(1)
#             arisu.monitor_message()  # 始监控
#             """消息处理"""
#             if len(arisu.message_processing_queues) > 0:  # 消息队列不为空，进行队列处理
#                 reply = ef.split_respond_msg()  # 解析需要回应的消息
#                 arisu.message_processing_queues.pop(0)  # 清理回应的消息(出队)[必须在split_respond_msg之后]
#                 """开始消息处理逻辑（不是聊天就是指令）"""
#                 # 非指令
#                 if not reply[3]:
#                     """聊天回复"""
#                     reply = deepseek.ask(f"{reply[0]}:{reply[1]}，时间:{reply[2]}", False)  # 发出请求并回应(这里不重复打印到屏幕上)
#                     arisu.send_message(reply)
#                 # 接收到了指令（检测指令是否存在）
#                 elif ef.is_order(reply[1]):  # 指令库里面检索指令(顺序不能反，因为指令可能带有参数)
#                     """指令操作"""
#                     # 分割指令和参数
#                     order, args = ef.split_order_args(reply[1])
#                     # 是否有权限调度指令(包括root和非root的指令)
#                     if ef.check_permission(order, reply[0]):  # 传入指令和发送者
#                         arisu.send_message(ef.execute_order(order, args))  # 传入指令执行后拿到返回结果并发送
#                     else:
#                         arisu.send_message("雑魚权限？真の杂鱼~🐟呢")  # 传入指令执行后拿到返回结果并发送
#                 else:
#                     """使用了不存在的指令(不是聊天也无法调用指令库的指令)"""
#                     print("接收到了一条不存在的指令(不是聊天也没有在指令库中找到指令)")
#                     arisu.send_message("不存在该指令")
#             else:
#                 pass  # print("出现新消息，这里不进行打印，因为监视方法已经打印了")
#
#
#     """进程创建"""
#     @staticmethod
#     def arisu_ai_auto_reply_task(print_widget: QTextBrowser, qq_group_name: str, bot_name: str, root: str,
#                                  exit_password: str, init_role: str,
#                                  qq_group_location: str, remove_dangerous_order: str):
#         """爱丽丝AI自动回复任务
#         is_task_progress ： 任务完成标志位（内存共享变量）
#         qq_group_name ：QQ群名
#         bot_name ：机器人名
#         root ：最高权限者
#         exit_password ：退出指令的密码
#         init_role ：初始人设
#         qq_group_location ：0,0（窗口的位置，文本的形式）
#         remove_dangerous_order ：False（布尔值）
#         """
#         """输出重定向"""
#         # sys.stdout = OutputRedirection()  # 实例化输出重定向
#         # sys.stdout.text_print.connect(print_widget.append)  # 传入输出窗口并打通信号
#         # print("\033[91m测试完成\033[0m")
#         """实例化对象"""
#         # print(qq_group_name, bot_name, root, exit_password, init_role, qq_group_location, remove_dangerous_order)
#         # deepseek消息回复(示例化对象没有顺序要求)
#         deepseek = DeepseekConversationEngine(init_role)  # 给deepseek这个外部变量赋值（让外部函数也能调用）
#
#         # qq消息监听者
#         arisu = QQMessageMonitor(qq_group_name, bot_name, 4)
#
#         # 外部函数(传入需要的对象)
#         ef = ArisuQQChatAICore(deepseek, arisu, root, exit_password, qq_group_location, remove_dangerous_order)
#
#         # 保持窗口(显示、位置、大小)，设置10秒进行一次保持
#         ef.thread_keep_win(sleep_time := 10)  # 我用个海象不过分
#         print(f"窗口位置:{ef.qq_group_x, ef.qq_group_y}\t保持原始窗口的刷新时间:{sleep_time}秒/刷")
#         """核心循环逻辑"""
#         # while is_task_progress.value:  # 使用.value访问共享变量的值:
#         while True:
#             """监听窗口控制"""
#             # 一秒监听一次窗口，防止CUP占用过高
#             sleep(1)
#             arisu.monitor_message()  # 始监控
#             """消息处理"""
#             if len(arisu.message_processing_queues) > 0:  # 消息队列不为空，进行队列处理
#                 reply = ef.split_respond_msg()  # 解析需要回应的消息
#                 arisu.message_processing_queues.pop(0)  # 清理回应的消息(出队)[必须在split_respond_msg之后]
#                 """开始消息处理逻辑（不是聊天就是指令）"""
#                 # 非指令
#                 if not reply[3]:
#                     """聊天回复"""
#                     reply = deepseek.ask(f"{reply[0]}:{reply[1]}，时间:{reply[2]}", False)  # 发出请求并回应(这里不重复打印到屏幕上)
#                     arisu.send_message(reply)
#                 # 接收到了指令（检测指令是否存在）
#                 elif ef.is_order(reply[1]):  # 指令库里面检索指令(顺序不能反，因为指令可能带有参数)
#                     """指令操作"""
#                     # 分割指令和参数
#                     order, args = ef.split_order_args(reply[1])
#                     # 是否有权限调度指令(包括root和非root的指令)
#                     if ef.check_permission(order, reply[0]):  # 传入指令和发送者
#                         arisu.send_message(ef.execute_order(order, args))  # 传入指令执行后拿到返回结果并发送
#                     else:
#                         arisu.send_message("雑魚权限？真の杂鱼~🐟呢")  # 传入指令执行后拿到返回结果并发送
#                 else:
#                     """使用了不存在的指令(不是聊天也无法调用指令库的指令)"""
#                     print("接收到了一条不存在的指令(不是聊天也没有在指令库中找到指令)")
#                     arisu.send_message("不存在该指令")
#             else:
#                 pass  # print("出现新消息，这里不进行打印，因为监视方法已经打印了")
#
#     def arisu_process_create(self, cup_core, process_args_list):
#         """爱丽丝进程创建
#         参数：
#         cup_core ： cpu核心数量
#         process_args_list ：进程参数列表
#         如：process_args = [
#             ("1", "爱丽丝", "雁低飞", "1", "爱丽丝Pro", "-724,-724", False),
#             ("2", "爱丽丝", "雁低飞", "1", "爱丽丝Pro", "-724,1", False),
#             ("3", "爱丽丝", "雁低飞", "1", "爱丽丝Pro", "-724,726", False),
#             ("4", "爱丽丝", "雁低飞", "1", "爱丽丝Pro", "-724,1451", False)
#                         ]
#         """
#         info("进程池创建成功")
#         process_list = list()  # 进程列表
#         with multiprocessing.Pool(processes=cup_core) as pool:
#             # 遍历创建进程的参数
#             for args in process_args_list:
#                 print(args)
#                 # 使用apply_async进行非阻塞调用（任务、所需参数）
#                 process = pool.apply_async(self.arisu_ai_auto_reply_task, args)
#                 # 把调度的进程添加进入进程列表列表里面
#                 process_list.append(process)
#         pool.join()
#         info("进程池已关闭")


def clear_temp():
    """删除残留在temp文件的MP4动态壁纸文件
    返回值：如果成功删除所有找到的缓存文件就返回True
    否则返回False（可能文件被正在使用或被添加了只读无法删除的权限等）
    """
    # 通过环境变量获取Windows临时文件夹路径
    temp_directory = os.environ.get("TEMP") or os.environ.get("TMP")

    # 构建匹配规则(python.6个字母.mp4),re.I为边界控制，使用后能从4.8ms变为2.9ms
    match_rule = re.compile(r"^python\.[a-zA-Z]{6}\.mp4$",re.I)

    # 遍历temp文件夹的所有符合匹配规则的文件，把符合的文件名构造成列表
    delete_files = [file_name for file_name in os.listdir(path=temp_directory) if re.search(match_rule, file_name)]

    flag = True # 成功卸载所有泄露文件的标志位
    # 开始删除泄露的文件
    for file_name in delete_files:  # 遍历需要删除的文件名
        try:
            # 文件绝对路径拼接后进行删除
            os.remove(os.path.join(temp_directory, file_name))
            info(f"成功删除意外溢出的文件:{file_name}")
        except PermissionError:
            # exception("文件正在被使用，以下是错误信息:")
            pass
        except(OSError,FileNotFoundError):
            exception("缓存文件(动态壁纸MP4文件)删除失败，以下是错误信息:")
    return True if flag else False



if __name__ == '__main__':
    clear_temp()