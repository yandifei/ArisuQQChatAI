""" configuration_manager.py  配置管理器
用来管理初始化数据和配置读写
"""
# 系统自带包
import configparser
import os


class ConfigurationManager:
    def __init__(self):
        """配置文件增删改查的操作"""
        """配置文件路径"""
        self.user_settings_path = "./用户设置/UserSettings.ini"  # 用户设置路径
        self.bind_path = "./用户设置/Bind.ini"  # 绑定配置路径
        self.keyboard_shortcut_path = "./用户设置/KeyboardShortcut.ini"  # 键盘快捷键配置路径
        self.encoding = "utf-8"  # 编码格式
        self.try_path()  # 路径检测
        """实例化解析器"""
        # user_settings(INI格式配置文件的解析器对象[严格区分大小写])
        self.user_settings = configparser.ConfigParser(allow_no_value=False, strict=True)
        self.user_settings.read(self.user_settings_path, encoding=self.encoding)  # 读入配置文件内容(指定编码格式是utf-8)
        # Bind(INI格式配置文件的解析器对象[严格区分大小写])
        self.bind = configparser.ConfigParser(allow_no_value=False, strict=True)
        self.bind.read(self.bind_path, encoding=self.encoding)  # 读入配置文件内容(指定编码格式是utf-8)
        # KeyboardShortcut(INI格式配置文件的解析器对象[严格区分大小写])
        self.keyboard_shortcut = configparser.ConfigParser(allow_no_value=False, strict=True)
        self.keyboard_shortcut.read(self.keyboard_shortcut_path, encoding=self.encoding)  # 读入配置文件内容(指定编码格式是utf-8)

        #
        #
        # print(self.KeyboardShortcut["运行和停止"]["running"])
        # print(self.KeyboardShortcut["运行和停止"]["stop"])
        # print(self.KeyboardShortcut["动态主页"]["running"])
        # print(self.KeyboardShortcut["动态主页"]["stop"])

        # # 更新值
        # config.set('database', 'host', '192.168.1.100')
        # config['settings']['timeout'] = '45.0'
        #
        # # 添加新键
        # config['settings']['threads'] = '4'
        #
        # # 删除键
        # config.remove_option('settings', 'debug')

        # # 使用字典批量更新键值
        # settings = {
        #     "bot_name": "爱丽丝1",
        #     "root": "爱丽丝1",
        #     "exit_password": "1",
        #     "init_role": "爱丽丝",
        #     "qq_group_location": "0,0",
        #     "remove_dangerous_order": "False"
        # }
        # config["1"].update(settings)

    """文件路径处理"""

    def try_path(self):
        """文件路径异常处理，用于生产环境和测试环境"""
        if not os.path.isfile(self.user_settings_path):  # 当前测试路径
            self.user_settings_path = "." + self.user_settings_path  # 更新路径
            self.bind_path = "." + self.bind_path  # 更新路径
            self.keyboard_shortcut_path += "." + self.keyboard_shortcut_path  # 更新路径

    """配置读取"""

    def original_interface_location(self):
        """原始界面位置
        返回值： {"Home": 1, "StateMonitor": 2, "KeyboardShortcut": 3, "QuestionLinks": 4, "Settings": 5}
        """
        return {
            "Home": self.user_settings["原始界面位置"]["主页"],
            "StateMonitor": self.user_settings["原始界面位置"]["状态监测"],
            "KeyboardShortcut": self.user_settings["原始界面位置"]["热键"],
            "QuestionLinks": self.user_settings["原始界面位置"]["问题链接"],
            "Settings": self.user_settings["原始界面位置"]["用户设置"]
        }

    def user_interface_location(self):
        """用户界面位置
        返回值： 如{"Home": 3, "StateMonitor": 1, "KeyboardShortcut": 5, "QuestionLinks": 4, "Settings": 2}
        """
        return {
            "Home": self.user_settings["用户界面位置"]["主页"],
            "StateMonitor": self.user_settings["用户界面位置"]["状态监测"],
            "KeyboardShortcut": self.user_settings["用户界面位置"]["热键"],
            "QuestionLinks": self.user_settings["用户界面位置"]["问题链接"],
            "Settings": self.user_settings["用户界面位置"]["用户设置"]
        }

    def get_bind_sections(self):
        """获得绑定ini文件里的所有节"""
        return self.bind.sections()

    def get_bind_keys(self, section: str):
        """重绑定配置文件获取一个节的所有键值
        section : Q群名（节的名字）
        bot_name : 机器人
        root : 最高权限者
        exit_password : 退出指令密码
        init_role : 初始人设
        qq_group_location : 窗口位置
        remove_dangerous_order : 移除危险指令真假值（文本类型）
        """
        return [
            section,                                        # Q群名（节的名字）
            self.bind[section]["bot_name"],                 # 机器人
            self.bind[section]["root"],                     # 最高权限者
            self.bind[section]["exit_password"],            # 退出指令密码
            self.bind[section]["init_role"],                # 初始人设
            self.bind[section]["qq_group_location"],        # 窗口位置
            self.bind[section]["remove_dangerous_order"]    # 移除危险指令真假值（文本类型）
                 ]


    """更新配置"""
    # 用户配置(不包括热键和Q群绑定信息)

    """写入硬盘"""

    def save_ini(self, ini_file_object, ini_path):
        """ini文件保存
        ini_file_object : ini文件对象（解析器对象）
        ini_path : 配置文件路径
        """
        # 写入文件（保留原有注释用config.read()先读取）
        with open(ini_path, "w", encoding=self.encoding) as config_file:
            ini_file_object.write(config_file)

    def save_user_settings_ini(self):
        """保存user_settings的ini文件"""
        # 写入文件（保留原有注释用config.read()先读取）
        with open(self.user_settings_path, "w", encoding=self.encoding) as config_file:
            self.user_settings.write(config_file)

    def save_bind_ini(self):
        """保存bind的ini文件"""
        # 写入文件（保留原有注释用config.read()先读取）
        with open(self.bind_path, "w", encoding=self.encoding) as config_file:
            self.bind.write(config_file)

    def save_keyboard_shortcut_ini(self):
        """保存keyboard_shortcut的ini文件"""
        # 写入文件（保留原有注释用config.read()先读取）
        with open(self.keyboard_shortcut_path, "w", encoding=self.encoding) as config_file:
            self.keyboard_shortcut.write(config_file)


if __name__ == '__main__':
    init = ConfigurationManager()  # 实例化初始
    print(init.get_bind_sections())
