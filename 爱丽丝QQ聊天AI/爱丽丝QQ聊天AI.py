"""界面启动图标"""
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass
#系统自带的包
# from time import sleep                                                      # 导入休眠的方法（防止不断循环CPU导致资源占用过高）
import sys
# 第三方库
from PyQt6.QtWidgets import QApplication, QTextBrowser                      # 界面处理类
# 自己的库
from UI.ExtendedUI  import ArisuUI                                          # 导入开发好的UI类
from arisu_logger import debug, info, warning, critical, exception          # 导入日志方法
# from deepseek_conversation_engine import DeepseekConversationEngine         # deepseek对话类
# from qq_message_monitor import QQMessageMonitor                             # QQ消息监听类
# from UI.arisu_qq_chat_ai_core import ArisuQQChatAICore                      # ui的拓展方法类
# from UI.functions import OutputRedirection                                  # 输出重定向的类


"""主进程UI设置和槽函数链接"""
arisu_app = QApplication(sys.argv)  # 管理控制事件流和设置(sys.argv控制台接收参数)
arisu_ui = ArisuUI("爱丽丝", True, "resources/Arisu.ui")
arisu_ui.show()                 # 界面展示
info("UI界面加载完成")
sys.exit(arisu_app.exec())      # 安全退出界面任务

# """main处理（可惜我最终是线程池处理的）
# 因为windows本身的原因，如果不在if __name__ == '__main__':下创建进程池会导致无限递归来创建子进程
# Windows缺乏类似Unix的fork()机制
# """
# if __name__ == '__main__':
#     """主进程UI设置和槽函数链接"""
#     arisu_app = QApplication(sys.argv)  # 管理控制事件流和设置(sys.argv控制台接收参数)
#     arisu_ui = ArisuUI("爱丽丝", True, "resources/Arisu.ui")
#
#     arisu_ui.show()  # 界面展示
#     info("UI界面加载完成")
#
#
#     """程序退出"""
#     # exit_num = arisu.exec()    # UI界面退出的代码(0为正常退出，1为非正常退出)
#     # if exit_num != 0:   # 非正常退出，清理壁纸资源
#     #     critical(f"非正常退出UI窗口，清理残留资源,UI退出代码：{exit_num}")
#     #     clear_temp()    # 清除缓存目录的MP4文件
#     # print(exit_num)
#     # sys.exit(exit_num)  # 安全退出界面任务
#     sys.exit(arisu_app.exec())  # 安全退出界面任务