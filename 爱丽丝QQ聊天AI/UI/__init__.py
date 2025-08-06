"""爱丽丝QQ机器人界面开发/__init__.py
爱丽丝QQ机器人主程序包初始化
包含全局配置和包导入优化
"""
__author__ = "yandifei"
# 核心模块的快捷导入路径
from .ExtendedUI import ArisuUI
from .arisu_qq_chat_ai_ui import ArisuQQCHatAIUI
from .functions import OutputRedirection # 输出重定向

__all__ = ["ArisuUI", "ArisuQQCHatAIUI", "functions", "OutputRedirection"]
