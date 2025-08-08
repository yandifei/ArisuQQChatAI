<div align="center">
  <h1 align="center">
    <img src="./展示项目的图片/爱丽丝.png" width="200"/>
    <br/>
    ArisuQQChatAI · 爱丽丝QQ聊天AI
  </h1> 
</div>

<br/>

<div align="center">
  <a href=https://www.microsoft.com/zh-cn/software-download/windows11><img alt="使用平台" src="https://img.shields.io/badge/platform-Windows11-blue?style=flat-square&color=00ffff"/></a>
  <a href=https://github.com/yandifei/ArisuQQChatAI/releases/download/v1.0.0-beta/ArisuQQChatAI.7z><img alt="最新版徽章" src="https://img.shields.io/github/release/yandifei/ArisuQQChatAI?include_prereleases&style=flat-square&color=4141dc"/></a>
  <a href=https://github.com/yandifei/ArisuQQChatAI/releases><img alt="总下载次数" src="https://img.shields.io/github/downloads/yandifei/ArisuQQChatAI/total?style=flat-square&color=00ffff" /></a>
</div>

<br/>

<div align="center">
  喜欢的话，就给爱丽丝个✨Star✨吧！ (ﾉ>ω<)ﾉ❤️<img alt="Total Downloads" src="./爱丽丝QQ聊天AI/resources/爱丽丝表情包/非女仆/14.png" width="50"/>
</div>

## 功能介绍

- **AI自动回复**：
  - 使用deepseek的api自动回复
  - 结合指令系统对回答进行优化
  - 可自定义人设和能记录上下文
  - 其余功能可以看：[DeepseekConversationEngine](https://github.com/yandifei/DeepseekConversationEngine)
- **自定回复策略**：
  - 关键词自动回复
  - 过滤回复指定发送者
  - 指定发送者发出消息就进行回复
  - 指定发送者及特定语句自动回复
- **权限系统**：
  - 需要承认的是权限系统存在设计缺陷：权限可被复制。(有解决方案，但价值和意义太低了)
  - 通过权限分级可以避免某些“危险指令”导致QQ封号(如：从禁漫天堂下本子发到Q群中)
- **指令系统**：
  - AI无法完成的操作(调整AI的回复策略)
  - 后续有功能再加(文件处理、电脑状态等)
- **异常处理与日志**：
  - 强大的纠错机制(全局异常捕获和线程池自动重启线程)
  - 消息日志记录(撤回前监测到的消息会被记录到日志中)

## 界面示意

<div style="display: flex; justify-content: center; gap: 10px; margin: 20px auto;">
  <img src="https://media.githubusercontent.com/media/yandifei/ArisuQQChatAI/bf40dda6d3300abe92f4e03f103e936f9738ee97/%E5%B1%95%E7%A4%BA%E9%A1%B9%E7%9B%AE%E7%9A%84%E5%9B%BE%E7%89%87/%E4%B8%BB%E9%A1%B5.png" 
       alt="热键"
       style="width: 500px; height: auto;"/>
  <img src="https://media.githubusercontent.com/media/yandifei/ArisuQQChatAI/main/%E5%B1%95%E7%A4%BA%E9%A1%B9%E7%9B%AE%E7%9A%84%E5%9B%BE%E7%89%87/%E7%8A%B6%E6%80%81%E7%9B%91%E6%B5%8B.png" 
      alt="绑定" 
      style="width: 500px; height: auto;"/>
  <img src="https://media.githubusercontent.com/media/yandifei/ArisuQQChatAI/main/%E5%B1%95%E7%A4%BA%E9%A1%B9%E7%9B%AE%E7%9A%84%E5%9B%BE%E7%89%87/%E7%BB%91%E5%AE%9A.png" 
       alt="绑定" 
       style="width: 500px; height: auto;"/>
</div>

## 安装使用
- 下载地址：[⚡Github下载⚡](https://github.com/yandifei/ArisuQQChatAI/releases/download/v1.0.0-beta/ArisuQQChatAI.7z)
- 直接解压即后打开“爱丽丝QQ聊天AI.exe”
- 确保你有deepseek api的密钥和这个密钥有钱
- 设置窗口录入deepseek api密钥并填写好绑定QQ群的参数
- 打开并登陆QQ，设置中在点击“超级调色盘”把主题选择为“极简白”
- 打开需要自动回复的Q群窗口，点击开启自
- 动回复按钮或一键开启按钮即可

## 项目运行
- 小白不用看这里。开发者用于异常崩溃输出和日志记录查询
- 也可以用pycharm中打开 爱丽丝QQ聊天AI 文件夹运行 爱丽丝QQ聊天AI.py
```git
# 1.克隆项目
git clone https://github.com/yandifei/ArisuQQChatAI.git

# 2.进入项目目录的开发目录（目录名需与克隆结果一致）
cd ArisuQQChatAI/爱丽丝QQ聊天AI/

# 3. [可选] 创建虚拟环境
conda create -n Arisu python=3.13.5
# 激活虚拟环境
conda activate Arisu

# 4.安装依赖（强烈建议使用虚拟环境）
pip install -r requirements.txt

# 5.启动项目
python 爱丽丝QQ聊天AI/爱丽丝QQ聊天AI.py
```

## 注意事项
- 更新就直接覆盖安装
- 必须在QQ中在点击“超级调色盘”把主题选择为“极简白”

## 免责声明
- ⚠️本软件通过 DeepSeek API 生成的内容不代表开发者观点，其准确性、适当性由使用者自行判断并承担全部责任。🤖AI可能产生错误、偏见或不适宜内容，开发者不对此引发的任何后果负责。
- 如果使用该软件导致Q号被封⚡，开发者不负任何责任！(非要作死开发者也拦不住，已提供移除危险指令的选项)🎭用户需要自行承当封号风险！！！
- 使用MIT协议📜保留原始版权可自由修改，🚫禁止将该项目用于引流(带节奏)、纯色情、当键政、消息轰炸等非法目的。
- 此软件的根本目的是打造接入DeepSeek的API接口实现“满分”🧠的问题解答和为用户提供《情绪价值💖》！


## 致谢

此项目的开发离不开以下项目
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- [Python-UIAutomation-for-Windows](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)
- [JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)

## 相关项目

- [DeepseekConversationEngine](https://github.com/yandifei/DeepseekConversationEngine) 基于deepseek api开发的类库

## 问题反馈
- 其实还有别的项目要研发和个人学习，没时间处理。
- 提交 [Issues](https://github.com/yandifei/ArisuQQChatAI/issues) 或 邮箱3058439878@qq.com