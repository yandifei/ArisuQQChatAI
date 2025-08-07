# pyinstaller --hidden-import comtypes --add-data "A:/Anaconda3/envs/Arisu/Lib/site-packages/comtypes;comtypes" --add-data "A:/Anaconda3/envs/Arisu/Lib/site-packages/uiautomation/bin;uiautomation/bin" -i ./resources/Logo/256.ico --uac-admin --noconsole -D 爱丽丝QQ聊天AI.py
"""
非必要不要加这个字段：--uac-admin  这个是添加管理员权限的（其实这里我觉得是必要得，非必要是pyinstaller文档）
pyinstaller -i .\文档\QQ_chat_AI.ico --splash .\文档\QQ_chat_AI.png --uac-admin -D QQ聊天AI.py
修改图标 + 启动图标 + 打包的主程序
打包后需要的exe在dist文件夹里面

打包出来后不能用的试试这个指令（我提示却这个组件）
pyinstaller --hidden-import comtypes --add-data "A:/Anaconda3/envs/Arisu/Lib/site-packages/comtypes;comtypes" --add-data "A:/Anaconda3/envs/Arisu/Lib/site-packages/uiautomation/bin;uiautomation/bin" -i ./resources/Logo/256.ico --splash ./resources/背景/爱丽丝的笑容.jpg --uac-admin --noconsole -D 爱丽丝QQ聊天AI.py

--hidden-import comtypes：强制包含 comtypes 模块。
--add-data：确保 comtypes 的附属文件被正确打包（路径需根据实际虚拟环境调整）。
"""


"""新打包指令
靠，还得添加其他可能的transformers子模块
transformers.models.auto
transformers.models.ernie_moe

pyinstaller --hidden-import comtypes --add-data "A:/Anaconda3/envs/Arisu/Lib/site-packages/comtypes;comtypes" --hidden-import=transformers.models.ernie4_5 --hidden-import=transformers.models.ernie.tokenization_ernie --add-data "A:/Anaconda3/envs/Arisu/Lib/site-packages/uiautomation/bin;uiautomation/bin" -i ./resources/Logo/256.ico --uac-admin --noconsole -D 爱丽丝QQ聊天AI.py
pyinstaller
--hidden-import comtypes --add-data "A:/Anaconda3/envs/Arisu/Lib/site-packages/comtypes;comtypes"
--hidden-import=transformers.models.ernie4_5
--hidden-import=transformers.models.ernie.tokenization_ernie
--add-data "A:/Anaconda3/envs/Arisu/Lib/site-packages/uiautomation/bin;uiautomation/bin"
-i ./resources/Logo/256.ico --uac-admin --noconsole -D 爱丽丝QQ聊天AI.py

-i ./resources/Logo/256.ico --splash ./resources/背景/爱丽丝的笑容.jpg --uac-admin --noconsole -D 爱丽丝QQ聊天AI.py
"""



"""
我 pip freeze 后输出的是乱码说明不是文件编码格式出问题了，是包元数据问题
升级 pip
python -m pip install --upgrade pip
不行，pip freeze 还是乱码
----------------------------看这里-------------------------------
终极方案：放弃 pip freeze，改用更牛逼的pipreqs
用 pipreqs 可以精准排除没用的模块
pip install pipreqs           # 安装工具
# 生成requirements.txt
pipreqs . --encoding=utf8 --force

--encoding=utf8：解决因编码问题导致的报错（如中文路径或注释）
--force：强制覆盖已存在的 requirements.txt 文件5
--ignore: 忽略指定目录（如虚拟环境 venv）

实际效果，确实叼，之前50几个依赖的，现在确实只有导入的依赖了，必须去给他个Start

如果已经有requirements.txt直接 pipreqs . 的话会报错，记得删除
我直接使用 pipreqs . 没有出现乱码的问题
"""
# import subprocess
# # 我这里生成的是GBK编码格式的文本，所以使用代码生成utf-8的requirements.txt(后面排查是我包元数据的问题)
# with open('requirements.txt', 'w', encoding='utf-8') as f:
#     subprocess.run(['pip', 'freeze'], stdout=f, text=True)
