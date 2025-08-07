"""管理API的类(对话和余额计算等)
1.密钥安全读取和校验
2.多模式对话管理（V3/R1）
3.温度参数动态调节
4.Token消耗精准计算
5.API资源监控预警
"""
# 内置库
import os
# 导入系统库# 禁用所有咨询类警告(针对None of PyTorch这个警告，官方方法)
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
import types    # 导入数据类型库
import json # 解析服务器的json文本回应
# 第三方库
import requests # 导入网络请求的库
import transformers # (爆红没事，能跑就行)
from openai import OpenAI, OpenAIError  # 导入OpenAI和OpenAI错误类型
# 额外的库
import keyring # 密钥获取


class DeepseekConversationEngine:
    def __init__(self,role=None):
        """初始化DeepseekConversationEngine
        参数：role ： 对话人设，这个可以选择默认值None(提示库下的文件名)
        参数：out ： 是否输出打印初始化成功
        :return: True
        """
        self.__DEEPSEEK_API_KEY = self.__keyring_get_key()    # 从系统环境变量中读入密钥和检查密钥
        """-----------------------------------------------------核心业务-----------------------------------------------------"""
        self.base_url ="https://api.deepseek.com"   # api网址
        """对话补全请求参数(回答内容控制)"""
        # 模型默认V3(deepseek-chat)，R1是(deepseek-reasoner)
        self.model_choice = "deepseek-chat"
        # 介于 -2.0 和 2.0 之间的数字。如果该值为正，那么新 token 会根据其在已有文本中的出现频率受到相应的惩罚，降低模型重复相同内容的可能性。
        self.frequency_penalty = 0  # 默认0
        # 介于 1 到 8192 间的整数，限制一次请求中模型生成 completion 的最大 token 数。输入 token 和输出 token 的总长度受模型的上下文长度的限制。
        self.max_tokens = 4096 #  默认4096个token（6825.667个字），8192为13653.33个字
        # 介于 -2.0 和 2.0 之间的数字。如果该值为正，那么新 token 会根据其是否已在已有文本中出现受到相应的惩罚，从而增加模型谈论新主题的可能性。
        self.presence_penalty = 0   # 默认0
        # response_format。一个 object，指定模型必须输出的格式。设置为 { "type": "json_object" } 以启用 JSON 模式，该模式保证模型生成的消息是有效的 JSON。
        self.response_format = {"type": "text"}   # 默认为text，{"type": "json_object"}强制 JSON 输出
        # 停止生成标志词，string 或最多包含 16 个 string 的 list。比如","则在生成这个字符 前 就停止生成
        self.stop = list()  # 为了方便统一，这里采用列表吧
        # 是否流式输出。如果设置为 True，将会以 SSE（server-sent events）的形式以流式发送消息增量。消息流以 data: [DONE] 结尾。
        self.stream = False
        # 只有在stream参数为true时才可设置此参数。如果设置为true，在流式消息最后的data: [DONE] 之前将会传输一个额外的块。此块上的 usage 字段显示整个请求的 token 使用统计信息
        self.stream_options = None # 请求用量统计(必须开启流式输出才能开)
        # temperature 参数默认为(1.0)代码生成/数学解题(0.0)数据抽取/分析(1.0)通用对话(1.3)翻译(1.3)创意类写作/诗歌创作(1.5)
        self.temperature = 1.3  # 默认日常聊天就设置为1.3了
        # 作为调节采样温度的替代方案，模型会考虑前 top_p 概率的 token 的结果。所以 0.1 就意味着只有包括在最高 10% 概率中的 token 会被考虑。 我们通常建议修改这个值或者更改 temperature，但不建议同时对两者进行修改。
        self.top_p = 1 # 默认值为1
        # 模型可能会调用的 tool 的列表。目前，仅支持 function 作为工具。使用此参数来提供以 JSON 作为输入参数的 function 列表。最多支持 128 个 function。
        self.tools = None   # 默认为None
        # 控制模型调用 tool 的行为。
        self.tool_choice  = "none"
        # 是否返回所输出 token 的对数概率。如果为 true，则在 message 的 content 中返回每个输出 token 的对数概率。
        self.logprobs = False
        # 一个介于 0 到 20 之间的整数 N，指定每个输出位置返回输出概率 top N 的 token，且返回这些 token 的对数概率。指定此参数时，logprobs 必须为 true。
        self.top_logprobs = None
        """FIM对话补全参数"""
        # 用于生成完成内容的提示(需要补 全的开头)
        self.prompt = None
        # 在输出中，把 prompt 的内容也输出出来
        self.echo = False
        # 制定输出中包含 logprobs 最可能输出 token 的对数概率，包含采样的 token。
        self.FIM_logprobs = 0
        # 制定被补 全内容的后缀。
        self.suffix = None
        """历史对话处理"""
        self.reasoning_content = ""   # 保存最近一次的思维链
        self.clear_flag = 5 # 对话历史最大数，超过就清空最开始的那一次的对话(V3默认为5轮)
        self.dialog_history = list()    # 对话历史，列表存储(这个对话历史其实就是message参数)
        self.role = None    # 用来存放当前人设(不知道当前人设的时候可以调用输出展示)
        if role is not None:    # 人设不为空
            self.role = self.role_read(role)  # 读取人设
            self.dialog_history.append({"role": "system", "content": self.role})   # 添加人设
        # 记得设置没有任何人设的对话
        """余额查询"""
        self.balance_inquiry_url = "https://api.deepseek.com/user/balance"  # 余额查询网址
        """Token分词和计算"""
        # add_special_tokens=True是模型输入格式要求,False是纯文本Token计算
        self.tokenizer = transformers.AutoTokenizer.from_pretrained("resources/deepseek_v3_tokenizer/", trust_remote_code=True)

    def reset(self, out = False):
        """初始化或格式化类的属性1
        参数 ： out ： 初始化后是否打印提示
        返回值：True
        """
        role =  self.role # 提前把人设拿出来
        self.__init__(None)    # 初始化所有参数，清空人设
        self.dialog_history.append({"role": "system", "content": role})  # 添加人设
        if out: print("初始化成功")
        return True


    """密钥安全读取和校验"""
    @staticmethod
    def __get_check_key():
        """私有方法（从系统环境变量中读入密钥和检查密钥）密钥有效就进行属性修改"""
        try:
            # 从环境变量获取密钥
            DEEPSEEK_API_KEY = os.environ['DEEPSEEK_API_KEY']  # 从环境变量读取deepseek的api密钥
        except KeyError:
            raise KeyError(f"未在环境变量中找到deepseek的api密钥，请确保添加成功，如果确认已经添加请重启pycharm或该程序")
        import requests
        # 测试请求到模型列表端点
        response = requests.get(
            "https://api.deepseek.com/user/balance",  # 请求网址
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}  # 请求头
        )
        if response.status_code != 200:  # 检查响应状态码
            raise ValueError("API密钥无效或未授权，检查密钥是否正确或重启pycharm或程序")
        return DEEPSEEK_API_KEY

    @staticmethod
    def __keyring_get_key():
        """使用keyring库获得密钥(私有方法)"""
        # print(f"已获取的API密钥")  # 不打印输出密钥显示避免泄露
        return keyring.get_password("DEEPSEEK_API_KEY", "爱丽丝")

    """对话输出参数"""
    def compatible_openai(self, out = False):
        """修改属性self.base_url对OpenAI进行兼容
        # 出于与 OpenAI 兼容考虑，您也可以将 base_url 设置为 https://api.deepseek.com/v1 来使用，
        但注意，此处 v1 与模型版本无关。
        参数：out ： 是否输出打印修改成功，默认False
        返回值：True
        """
        self.base_url = "https://api.deepseek.com/v1"
        if out: print("已切换至兼容模式")
        return True

    def use_beat(self, out = False):
        """修改self.base_url属性为"https://api.deepseek.com/beta"来开启api某些限制功能
        部分功能必须是beat才能开启，如R1思维返回就必须使用这个url
        参数：out ： 是否输出打印修改成功，默认False
        返回值：True
        """
        self.base_url = "https://api.deepseek.com/beta"
        if out: print("已切换测试接口")
        return True

    # 对话补充模式
    def set_model(self, model, out = False):
        """模型切换(V3或R1)，需要给定指定模型参数
        参数：model ： 模型的名字(V3或R1)
        out ： 是否输出打印修改成功，默认False
        返回值：修改错误返回False，成功修改返回True
        """
        if model != "V3" and model != "R1":
            if out: print("\033[91m不存在该模型，不对该参数进行任何修改\033[0m")
            return False
        elif model == "V3":
            if out: print("已切换至V3模型")
            self.clear_flag = 5  # 对话历史最大数，超过就清空最开始的那一次的对话(V3默认为5轮)
            self.model_choice = "deepseek-chat" # V3模型
        elif model == "R1":
            if out: print("已切换至R1模型")
            self.clear_flag = 10  # 对话历史最大数，超过就清空最开始的那一次的对话(R1默认为10轮)
            self.model_choice = "deepseek-reasoner"  # R1模型
        return True

    def switch_model(self, out = False):
        """模型切自动换，如果为 V3 模型就切换为 R1模型， 如果为 R1 模型则切换为 V3模型
        模型默认V3(deepseek-chat)，R是(deepseek-reasoner)
        参数：out ： 是否打印修改提示，默认False
        返回值：True
        """
        if self.model_choice == "deepseek-chat":  # 本身就是V3模型
            self.model_choice = "deepseek-reasoner" # 切换为R1模型
            self.clear_flag = 10  # 对话历史最大数，超过就清空最开始的那一次的对话(R1默认为10轮)
            if out: print(f"已切换至R1模型")
        # elif self.model_choice == "deepseek-reasoner":    # 本身就是R1模型:
        else:
            self.model_choice = "deepseek-chat" # 切换为V3模型
            self.clear_flag = 5  # 对话历史最大数，超过就清空最开始的那一次的对话(V3默认为5轮)
            if out: print(f"已切换至V3模型")
        return True

    def set_frequency_penalty(self, frequency_penalty = 0.0):
        """控制生成内容的重复性 -2.0（鼓励重复）到 2.0（严格避免重复）、0（无惩罚）
       在新 token 会根据其在已有文本中的出现频率受到相应的惩罚，降低模型重复相同内容的可能性。
       参数：frequency_penalty ： 默认0.0
       返回值：修改错误返回False，成功修改返回True
       """
        if frequency_penalty < -2 or frequency_penalty > 2:
            print("\033[91m参数不在有效范围内(-2.0至2.0)，不对该参数进行任何修改\033[0m")
            return False
        self.frequency_penalty = frequency_penalty
        return True

    def set_max_tokens(self, max_tokens : int = 4096, out = False):
        """修改输出最大token数(1-8192)
        参数 ： max_tokens ： 默认4096个token（6825.667个字），8192个token为13653.33个字
        out : 修改错误时是否打印输出参数范围
        返回值：修改错误返回False，成功修改返回True
        """
        max_tokens = int(max_tokens)    # 先强制转为整型
        if max_tokens < 1 or max_tokens > 8192: # 不在1-8192的范围内
            if out: print("\033[91m参数不在范围内(1-8192)，不对该参数进行任何修改\033[0m")
            return False
        self.max_tokens = max_tokens
        if out: print(f"已修改修改输出最大token数为{max_tokens}")
        return True

    def set_presence_penalty(self, presence_penalty = 0.0):
        """对模型是否产生新内容进行打分，介于 -2.0 和 2.0 之间的数字。
        如果该值为正，那么新 token 会根据其是否已在已有文本中出现受到相应的惩罚，从而增加模型谈论新主题的可能性。
        参数： presence_penalty ：-2.0到2.0，默认0.0
        返回值：修改错误返回False，成功修改返回True
        """
        if presence_penalty < -2 or presence_penalty > 2:
            print(f"\033[91m参数有误，打分范围在-2.0到2.0之间，不对该参数进行任何修改\033[0m")
            return False
        self.presence_penalty = presence_penalty
        return True

    def score_answer(self, score: int = 50, out = False):
        """对回答进行打分，不过这个是百分制
        分数越高重复内容越少，新话题也多。分数越低重复内容越多，新话题越少
        参数：score ： 0-100之间的数，默认50
        out : 是否打印输出修改提示
        返回值：超出返回False，修改成功返回True
        """
        score = int(score)  # 先强制转为整型
        if score < 0 or score > 100:    # 小于0或大于100
            if out: print("\033[91m超出打分范围([0-100]分,默认50分)\033[0m")
            return False
        # 这里就直接结合2个参数使用好了(重复内容和新话题)
        self.frequency_penalty = round(((score * 0.4) - 20) / 10, 1)      # 对结果进行四舍五入
        self.presence_penalty = round(((score * 0.4) - 20) / 10, 1)      # 对结果进行四舍五入
        if out: print(f"已给此次回答评分为{score}")
        return True

    def set_response_format(self, response_format = "text", out = False):
        """指定模型必须输出的格式("text"或"json")
        参数： response_format ： 默认 "text",字符串格式，可填"json"
        out : 修改错误时是否输出参数范围
        返回值：修改错误返回False，成功修改返回True
        """
        if response_format == "text" or response_format == "json_object":
            self.response_format = {"type": response_format}
            if out: print(f"已指定模型必须输出的格式为{response_format}")
            return True
        if out: print(f"\033[91m参数有误，指定模型必须输出的格式为\"text\"或\"json_object\"，不对该参数进行任何修改\033[0m")
        return False

    def set_stop(self, stop = None, out = False):
        """停止生成标志词
        参数： stop ： 可以是单个字符，也可以是字符组成的列表（敏感词最多16个）
        out : 是否打印修改提示，默认False
        返回值：修改错误返回False，成功修改返回True
        """
        if isinstance(stop, list) and (len(stop) + len(self.stop)) > 16:    # 如果是列表或
            if out: print(f"\033[91m停止标志词最多16，当前{len(self.stop)}个，添加后超出最大值\033[0m")
            return False
        elif isinstance(stop, list):    # 输入的是列表
            self.stop.extend(stop)  # 把列表添加进去
        self.stop.append(stop)  # 添加敏感词
        if out: print(f"添加成功，当前敏感字词：{self.stop}个")
        return True

    def del_stop(self, stop, out = False):
        """删除敏感词
        参数 ： stop : 选需要删除的敏感词
        out : 是否打印修改提示，默认False
        这个词不存在也会返回False,不存在可删的列表返回False，否则删除敏感词后返回True
        """
        if isinstance(self.stop,list) and len(self.stop) == 0:  # 没有可以删除的提示词
            if out: print("敏感词列表为空，没有可以删除的敏感词")
            return False
        elif stop not in self.stop:
            if out: print("敏感词不存在")
            return False
        else:
            self.stop.remove(stop)
            if out: print("删除成功")
        return True

    def set_stream(self, stream = False, out = False):
        """是否流式输出。如果设置为 True，将会以 SSE（server-sent events）的形式以流式发送消息增量。消息流以 data: [DONE] 结尾。
        参数： stream ： 默认为False(不开启流式)
        out : 是否输出修改完成，默认为False
        返回值：修改错误返回False，成功修改返回True
        """
        if not isinstance(stream, bool):
            print("\033[91m参数有误，True或False，不对该参数进行任何修改\033[0m")
            return False
        elif stream and out:
            print("已开启流式输出")
        elif out:
            print("已开启非流式输出")
        self.stream = stream
        return True

    def set_stream_options(self, stream_options = None, out = False):
        """流式消息最后的data多一个usage 字段，这个字段包括token 使用统计信息
        参数： stream_options ： 默认为None(不返回这个usage 字段),只能填None或True
        out : 是否打印修改提示，默认为False
        返回值：修改成功返回True，否则返回False
        """
        if not stream_options:  # 如果为假
            if out: print("已关闭请求用量统计")
            self.stream_options = None
            return True
        elif not self.stream:     # self.stream必须为True(开启流式才能开启这个选项)
            if out: print("\033[91m必须先开启流式(stream)才能开启修改开启这个字段\033[0m")
            return False
        elif not isinstance(stream_options, bool):
            if out: print("\033[91m参数有误，True或False，不对该参数进行任何修改\033[0m")
            return False
        if out: print("已开启请求用量统计")
        self.stream_options = {"include_usage": True}
        return True

    def set_temperature(self, temperature: float = 1.0, out = False):
        """设置模型对话的温度
        默认为(1.0)代码生成/数学解题(0.0)数据抽取/分析(1.0)通用对话(1.3)翻译(1.3)创意类写作/诗歌创作(1.5)
        参数 ： temperature ： 温度参数。直接调用就是设置为1.0
        out : 是否提示修改成功或失败, 默认为False
        返回值：如果修改成功返回True，否则返回False
        """
        temperature = float(temperature)    # 怕字符串，先强转
        if temperature < 0.0 or temperature > 2.0:
            if out: print("\033[91m超出温度范围(0.0-2.0),不对该参数进行任何修改\033[0m")
            return False
        else:
            if out: print(f"温度已修改为{temperature}")
            self.temperature = temperature
            return True # 显式返回

    def set_top_p(self, top_p = 1.0, out = False):
        """作为调节采样温度的替代方案，模型会考虑前 top_p 概率的 token 的结果。
        所以 0.1 就意味着只有包括在最高 10% 概率中的 token 会被考虑。我们通常建议修改这个值或者更改 temperature，但不建议同时对两者进行修改。
        参数： top_p ： 默认为1(0.0-1.0)
        out : 是否提示修改结果,默认False
        返回值：如果修改成功返回True，否则返回False
        """
        top_p = float(top_p)  # 怕字符串，先强转
        if top_p < 0 or top_p > 1:
            if out: print("\033[91m参数不在调用范围(0-1),不对该参数进行任何修改\033[0m")
            return False
        self.top_p = top_p
        if out: print(f"已将采样温度修改为{top_p}")
        return True

    def set_tools(self, tools = None, out = False):
        """模型可能会调用的 tool 的列表。目前，仅支持 function 作为工具。使用此参数来提供以 JSON 作为输入参数的 function 列表。最多支持 128 个 function。
        返回值：如果修改成功返回True，否则返回False
        out : 是否提示修改结果,默认False
        """
        self.tools = tools
        if out: print("修改成功")
        return True

    def set_tool_choice(self, tool_choice = "none"):
        """控制模型调用 tool 的行为。
        none 意味着模型不会调用任何 tool，而是生成一条消息。
        auto 意味着模型可以选择生成一条消息或调用一个或多个 tool。
        参数 ： tool_choice ： 默认"none"，有工具时填入"auto"
        返回值：如果修改成功返回True，否则返回False
        """
        if tool_choice != "none" or tool_choice != "auto":
            print("\033[91m参数错误,有工具为\"auto\"无工具为\"none\",不对该参数进行任何修改\033[0m")
            return False
        self.tool_choice = "none"
        return True

    def switch_tool_choice(self,  out = False):
        """自动切换模型调用 tool 的行为
        参数 ： out ： 是否打印修改输出,默认False
        """
        if self.tool_choice == "none":
            if out: print("已开启工具调用")
            self.tool_choice = "auto"
            return True
        if out: print("已关闭工具调用")
        self.tool_choice = "none"
        return True

    def set_logprobs(self, log_probs = False, out = False):
        """是否返回所输出 token 的对数概率。如果为 true，则在 message 的 content 中返回每个输出 token 的对数概率。
        参数：log_probs ： 默认False
        out ： 是否打印修改输出,默认False
        返回值：如果修改成功返回True，否则返回False
        """
        if not isinstance(log_probs,bool):
            if out: print("\033[91m参数错误,参数不是True或False,不对该参数进行任何修改\033[0m")
            return False
        elif log_probs:
            if out: print("已开启对数概率输出")
        elif not log_probs:
            print("已关闭对数概率输出")
        self.logprobs = log_probs
        return True

    def set_top_logprobs(self, top_logprobs =None , out = False):
        """一个介于 0 到 20 之间的整数 N，指定每个输出位置返回输出概率 top N 的 token，且返回这些 token 的对数概率。
        指定此参数时，logprobs 必须为 true。
        参数：top_logprobs ： 默认为None
        out ： 是否打印修改输出,默认False
        返回值：如果修改成功返回True，否则返回False
        """
        if top_logprobs: top_logprobs = int(top_logprobs)   # 如果值不为空或不为None则转换
        if top_logprobs is None:
            self.top_logprobs = None
            return True
        elif not self.logprobs:
            if out: print("\033[91m无效修改，必须先开启对数概率输出才能修改\033[0m")
            return False
        elif top_logprobs < 0 or top_logprobs > 20:
            if out: print("\033[91m参数不在调用范围(0-20),不对该参数进行任何修改\033[0m")
            return False
        self.top_logprobs = top_logprobs
        return True

    # FIM补充
    def set_prompt(self, prompt: str = "", out = False):
        """修改self.prompt的方法
        参数: prompt : 开头
        out : 是否输出，默认False
        返回值：修改成功返回True，否则返回False
        """
        if prompt is None or "":    # 补 全开头不能为空
            if out: print("\033[91m补全开头不能为空\033[0m")
            return False
        if out: print(f"已将开头修改为“{prompt}”")
        self.prompt = prompt
        return True

    def set_echo(self, echo = False, out = False):
        """在输出中，把 prompt 的内容也输出出来
        参数：echo : 默认False,
        out ： 是否打印修改输出,默认False
        返回值：返回True
        """
        if echo:
            self.echo = None    # 因为服务器那边不接受True，只接受False和None
        self.echo = True
        if out: print("因为服务器那边不接受True，只接受False和None,所以这个功能无效")
        return True

    def set_FIM_logprobs(self, FIM_logprobs : int = 0, out = False):
        """制定输出中包含 logprobs 最可能输出 token 的对数概率，包含采样的 token。最大20
        参数：FIM_logprobs : 默认0,最大20
        out ： 是否打印修改输出,默认False
        返回值：如果修改成功返回True，否则返回False
        """
        FIM_logprobs = int(FIM_logprobs)    # 先强制转为整型
        if FIM_logprobs < 0 or FIM_logprobs > 20:
            if out: print("\033[91m参数不在调用范围(0-20),不对该参数进行任何修改\033[0m")
            return False
        if out: print(f"已制定输出中保留{FIM_logprobs}个最可能输出token的对数概率")
        self.FIM_logprobs = FIM_logprobs
        return True

    def set_suffix(self, suffix = None, out = False):
        """修改self.suffix的方法
        参数: suffix : 后缀(默认为None)
        out : 是否输出，默认打开False
        返回值：没有后缀就返回False，有则返回True
        """
        if suffix is None or suffix == "":
            self.suffix = ""    # 设置为""防止报错
            if out:
                print("不设置后缀")
            return False
        if out:
            print(f"已将后缀修改为“{suffix}”")
        self.suffix = suffix
        return True

    # 对话内容构建(message组成)
    def add_role(self, role_txt):
        """添加角色扮演的提示（提示库 ）
        参数： role_txt : 角色扮演词
        """
        self.dialog_history.append({"role": "system", "content": role_txt})

    def add_answer(self, answer):
        """添加deepseek回答记录
        参数： answer ： AI回答文本
        """
        self.dialog_history.append({"role": "assistant", "content": answer})

    def add_question(self, question):
        """添加用户提出的问题
        参数： question ： 用户的问题
        """
        self.dialog_history.append({"role": "user", "content": question})
    """多人设、多模式对话管理(核心业务)"""
    def ask(self, ask_content, out = False):
        """用户发起提问
        参数 ： ask_content ： 用户提问的内容
        out : 是否打印到屏幕上
        返回值：assistant_content  ： 返回AI回答的结果
        如果调用失败会返回False
        """
        # 把用户的问题添加的历史记录里面去
        self.dialog_history.append({"role": "user", "content": ask_content})
        try:
            client = OpenAI(api_key=self.__DEEPSEEK_API_KEY, base_url=self.base_url)
            response = client.chat.completions.create(
                messages = self.dialog_history,
                model=self.model_choice,
                frequency_penalty = self.frequency_penalty,
                max_tokens = self.max_tokens,
                presence_penalty = self.presence_penalty,
                response_format = self.response_format,
                stop = self.stop,
                stream = self.stream,  # 是否流式输出(是否逐字输出)
                stream_options = self.stream_options,
                temperature = self.temperature,
                top_p = self.top_p,
                tools = self.tools,
                tool_choice = self.tool_choice,
                logprobs = self.logprobs,
                top_logprobs = self.top_logprobs
            )
            self.reasoning_content = ""  # 每次调用后都清空之前思维链(R1的推理内容)[确保最近一次对话存在思维链]
            assistant_content = ""  # 临时文本(记录或拼接)
            if not self.stream: # 非流式输出记录
                assistant_content = response.choices[0].message.content     # 拿到回答结果
                if out: print(assistant_content)        # 打印回答结果
                if self.model_choice == "deepseek-reasoner":     # R1模型会产生思维链（存在推理内容）
                    self.reasoning_content = response.choices[0].message.reasoning_content  # 把非流式的思维链接进行保存
            elif self.stream:   #流式输出
                if self.model_choice == "deepseek-reasoner":     # R1模型会产生思维链（存在推理内容）
                    for chunk in response:  # 遍历流式返回的每个数据块
                        # 确保流式中返回的空数据块(None)不会影响输出就加or ""
                        if out: print(f"{chunk.choices[0].delta.content or ""}", end="", flush=True)  # 实时逐词输出
                        assistant_content += chunk.choices[0].delta.content or "" # 累积最终回答
                        self.reasoning_content += chunk.choices[0].delta.reasoning_content or "" # 累积推理过程
                else:   # V3模型没有思维链
                    for chunk in response:  # 遍历流式返回的每个数据块
                        # 确保流式中返回的空数据块(None)不会影响输出就加or ""
                        if out: print(f"{chunk.choices[0].delta.content or ""}", end="", flush=True)  # 实时逐词输出
                        assistant_content += chunk.choices[0].delta.content or "" # 累积最终回答
                if out: print() # 打印换行
            self.dialog_history.append({"role": "assistant", "content": assistant_content}) # 添加AI的回答历史（包括流式和非流式的）
            # print(f"\033[91m{assistant_content}\033[0m")
            return assistant_content    # 返回AI回答的结果
        except OpenAIError as Error:
            # 获取 HTTP 状态码
            status_code = Error.status_code
            # print(f"错误码: {status_code}")
            # 根据状态码处理不同错误
            if status_code == 400:
                print("\033[91m请求体格式错误，请根据错误信息提示修改请求体\033[0m")
                assistant_content =  "请求体格式错误，请根据错误信息提示修改请求体"
            elif status_code == 401:
                print("\033[91mAPIkey错误，认证失败。请检查您的APIkey是否正确如没有APIkey请先创建APIkey\033[0m")
                assistant_content =  "APIkey错误，认证失败。请检查您的APIkey是否正确如没有APIkey请先创建APIkey"
            elif status_code == 402:
                print("\033[91m账号余额不足，请确认账户余额，并前往充值页面进行充值\033[0m")
                assistant_content =  "账号余额不足，请确认账户余额，并前往充值页面进行充值"
            elif status_code == 422:
                print("\033[91m请求体参数错误，请根据错误信息提示修改相关参数\033[0m")
                assistant_content =  "请求体参数错误，请根据错误信息提示修改相关参数"
            elif status_code == 429:
                print("\033[91m请求速率（TPM 或 RPM）达到上限，请合理规划您的请求速率\033[0m")
                assistant_content =  "请求速率（TPM 或 RPM）达到上限，请合理规划您的请求速率"
            elif status_code == 500:
                print("\033[91m服务器内部故障，请等待后重试。若问题一直存在，请联系我们解决\033[0m")
                assistant_content =  "服务器内部故障，请等待后重试。若问题一直存在，请联系我们解决"
            elif status_code == 503:
                print("\033[91m服务器负载过高，请稍后重试您的请求\033[0m")
                assistant_content =  "服务器负载过高，请稍后重试您的请求"
            else:
                print(f"\033[91m未知错误: {Error}\033[0m")
                assistant_content = f"未知错误: {Error}"

            # 把这次错误添加AI的回答历史（包括流式和非流式的）
            assistant_content = "此次请求过程中发生严重错误:" + assistant_content
            self.dialog_history.append({"role": "assistant", "content": assistant_content})
            return assistant_content  # 调用失败返回失败信息

    def fill_in_the_middle_ask(self):
        """FIM补 全（Beta）场景：代码补 全、文本填充（如生成函数逻辑、补 全模板中间内容）。
        精准填充文本中间的缺失部分（例如补 全函数体）。适合结构化内容生成（如代码、JSON）。
        注：只能单次对话，不具有上下文对话记录的功能。使用方法修改开头或结尾
        self.prompt，开头。self.suffix，结尾（不是必填的）。
        返回值: response_content : 补 全对话后的内容(完整版)
        如果补充开头为空返回FaLse
        """
        if not self.prompt: # 补充开头为空或None
            print("\033[91m补全开头不能为空\033[0m")
            return False
        try:
            client = OpenAI(api_key=self.__DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/beta")
            response = client.completions.create(
                model="deepseek-chat",
                prompt = self.prompt,       # FIM补全特有
                echo = self.echo,           # FIM补全特有
                frequency_penalty = self.frequency_penalty,
                logprobs = self.FIM_logprobs,
                max_tokens = self.max_tokens,
                presence_penalty = self.presence_penalty,
                stop = self.stop,
                stream = self.stream,
                stream_options = self.stream_options,
                suffix = self.suffix,       # FIM补全特有
                temperature = self.temperature,
                top_p = self.top_p
            )
            response_content = self.prompt  # 流式回复内容拼接(默认拼接给的开头)
            if not self.stream:  # 非流式输出记录
                response_content = response_content + response.choices[0].text + self.suffix
                print(response_content)
            else:   # 流式输出
                print(self.prompt, end="")   # 拼接开头
                for chunk in response:  # 遍历流式返回的每个数据块
                    print(f"{chunk.choices[0].text or ""}", end="", flush=True)  # 实时逐词输出
                    response_content += chunk.choices[0].text or "" # or "" 防止为None报错
                print(self.suffix) # 拼接结尾和换行(使用流式输出后得换行)
                response_content += self.suffix or "" # 拼接给的结尾(结尾可能为None)
            self.prompt = self.suffix =""   # 清空补充开头和补充结尾(因为是单次调用)
            return response_content # 返回回答后的问本
        except OpenAIError as Error:
            # 获取 HTTP 状态码
            status_code = Error.status_code
            # print(f"错误码: {status_code}")
            # 根据状态码处理不同错误
            if status_code == 400:
                print("\033[91m请求体格式错误，请根据错误信息提示修改请求体\033[0m")
            elif status_code == 401:
                print("\033[91mAPIkey错误，认证失败。请检查您的APIkey是否正确如没有APIkey请先创建APIkey\033[0m")
            elif status_code == 402:
                print("\033[91m账号余额不足，请确认账户余额，并前往充值页面进行充值\033[0m")
            elif status_code == 422:
                print("\033[91m请求体参数错误，请根据错误信息提示修改相关参数\033[0m")
            elif status_code == 429:
                print("\033[91m请求速率（TPM 或 RPM）达到上限，请合理规划您的请求速率\033[0m")
            elif status_code == 500:
                print("\033[91m服务器内部故障，请等待后重试。若问题一直存在，请联系我们解决\033[0m")
            elif status_code == 503:
                print("\033[91m服务器负载过高，请稍后重试您的请求\033[0m")
            else:
                print(f"\033[91m未知错误: {Error}\033[0m")
        return False

    def reasoning_content_output(self, out = False):
        """思考内容输出
        参数 ： out ： 是否打印输出提示，默认为False
        返回值：如果存在思维链接就返回内容，否则返回False
        """
        if self.reasoning_content == "" or self.reasoning_content is None:  # 思维链为空或None
            if out: print("最近的一次对话没有思考内容(思维链)")
            return False
        else:
            if out: print(f"思考内容(思维链):{self.reasoning_content}")
            return f"思考内容(思维链):{self.reasoning_content}"

    def set_dialog_history(self, dialog_round = 5, out = False):
        """设置对话最大轮次(必须是一个整数值，如果解除限制就填-1)
        参数 : round ； 设置的最大对话轮次，默认值为5
        out ： 是否输出修改成功或失败,默认False
        返回值: True
        """
        dialog_round = int(dialog_round)    # 先强制转换
        if dialog_round== -1:
            if out: print("\033[91m已解除对话轮次限制，注意最大token数和高额消费\033[0m")
            self.clear_flag = -1
        elif dialog_round < -1:
            print("\033[91m无法设置对话轮次为负数\033[0m")
            return False
        else:
            if out: print(f"\033[93m已设置对话轮次为{dialog_round}轮\033[0m")
            self.clear_flag = dialog_round
        return True

    def dialog_history_manage(self, out = False):
        """多轮对话管理，判断是否删除最旧的一轮对话，V3是5轮，R1是10轮
        返回值： 如果self.dialog_history为"max"意味这不需要进行删除
        out ： 是否输出修改成功或失败,默认False
        """
        if self.dialog_history == -1:  # 全增量记录
            if out: print("\033[33m已开启全增量记录，注意避免高额消费\033[0m")
            return True
        while int(len(self.dialog_history) / 2) > self.clear_flag:  # 超过对话轮次了
            if self.role is not None:   # 人设不为空的情况
                del self.dialog_history[1:3]    # 删除最开始的一轮对话(0是我人设(不能删)，1是我的提问，2是AI回答，不会到达3)
            else:   # 人设为空（没有设置人设）
                del self.dialog_history[0:2]    # 删除最开始的一轮对话(0是我的提问，1是AI回答，不会到达2)
        if out: print("处理完毕")
        return True

    def print_dialog_history(self,out = False):
        """打印聊天历史记录(仅仅打印聊天内容)
        参数： out ： 是否输出修改成功或失败,默认False
        返回值:一个列表格式是字符串(聊天内容)
        如果没有聊天记录就不进行打印
        """
        # {"role": "system", "content": role_txt}
        dialog_history = list() # 放置聊天记录
        temp_list = self.dialog_history  # 临时列表用来检查是否有人设
        if len(self.dialog_history) == 0:       # 没有人设情况且没有聊天记录(如果有聊天记录也会跳过下面的elif)
            if out: print("\033[91m当前没有任何聊天记录\033[0m")
            return False
        elif self.dialog_history[0]["role"] == "system":  # 设置了人设
            temp_list = self.dialog_history[1:]  # 排除人设
            if len(temp_list) == 0:   # (有人设的情况)没有聊天记录，无法打印
                if out: print("\033[91m当前没有任何聊天记录\033[0m")
                return False
        for ont_record in temp_list:  # 遍历聊天历史
            split_record = f'{"用户" if ont_record["role"] == "user" else "AI"}:{ont_record["content"]}'
            if out: print(split_record) # 打印记录
            dialog_history.append(split_record) # 添加到列表
        return dialog_history

    def clear_dialog_history(self, out = False):
        """清空历史记录（不包括人设）
        参数 ： out ： 是否输出修改成功或失败,默认False
        返回值： 如果历史为空则返回False,否则为True
        """
        if len(self.dialog_history) == 0:   # 对话记录为空
            if out: print("\033[91m对话历史为空无需清空\033[0m")
            return False
        if self.dialog_history[0]["role"] == "system":  # 设置了人设
            self.dialog_history = self.dialog_history[0:1]  # 切片清空除人设外的对话记录
        else:
            self.dialog_history.clear() # 直接清空，没有任何
        if out: print("已清空历史记录")
        return True

    @staticmethod
    def role_read(txt_file_name):
        """提示库角色设定读取
        参数：txt_file_name ： txt文本文件名字(默认放在“提示库”的文件夹中)，不需要填后缀名
        返回值 ： role_information : 文本文件的内容
        """
        while True:
            txt_file_name += ".txt"  # 补足后缀名
            path = os.path.join("用户设置/提示库/", txt_file_name)
            # path = os.path.join("../提示库/", txt_file_name)  # 上级目录
            if not os.path.isfile(path):  # 检查是否有这个文件（文件不存在）
                print(f"\033[91m\"{os.path.join(os.getcwd(), "提示库")}\"中没有“{txt_file_name}”这个文件，请检查该txt文件是否存在\033[0m")
                # txt_file_name = input("\033[92m请重新输入文件名(不用输入全名，路径自动补足)：\033[0m")
            else:  # 检查是否有这个文件（文件存在）:
                break  # 跳出循环
        with open(path, "r", encoding="utf-8") as role_txt:
            return role_txt.read()

    def role_switch(self, role_name):
        """人设切换(从提示库中读取人设并切换)
        参数： role_name ： 人设名
        返回值： 修改成功返回True，否者返回False
        """
        role_name_txt = role_name + ".txt"  # 补足后缀名
        path = os.path.join("用户设置/提示库/", role_name_txt)
        if not os.path.isfile(path):  # 检查是否有这个文件（文件不存在）
            print("提示库不存在该人设，不对人设进行任何任何修改")
            return False
        self.role = self.role_read(role_name)   # 修改人设属性
        # 在对话中启用人设
        if len(self.dialog_history) == 0:  # 没有任何对话记录，对开头进行人设添加
            self.dialog_history.append({"role": "system", "content": self.role})
        elif len(self.dialog_history) > 0:  # 存在对话记录不确定有没有之前的人设
            if self.dialog_history[0]["role"] == "system":  # 设置了人设
                self.dialog_history[0] = {"role": "system", "content": self.role}  # 把之前的人设替换掉
            else:  # 在消息头插入人设
                self.dialog_history.insert(0, {"role": "system", "content": self.role})
        print(f"已切换人设为：{role_name}")
        return True

    @staticmethod
    def role_list(out = False):
        """打印并返回提示库里面的所有人设
        参数 ： out ： 是否输出修改成功或失败,默认False
        返回值：如果人设库为空则返回False,成功读入则返回列表
        """
        all_role_list = list()  # 创建放置人设的列表
        for role_txt in os.listdir("用户设置/提示库/"):  # 遍历该文件夹所有文件
            if role_txt.endswith(".txt"):  # 检索后缀名为.txt的文件
                rol_name = role_txt.replace(".txt", "")  # 把文件名的.txt替换掉
                all_role_list.append(rol_name)  # 存放人设
        if len(all_role_list) == 0:
            if out: print("\033[91m\提示库中为空，不存在任何人设\033[0m")
            return False
        print("提示库的所有人设:",end=" ")
        if out: # 是否打印输出
            for role_name in all_role_list:
                print(role_name,end=" ")
            print() # 换行
        return all_role_list

    @staticmethod
    def select_role_content(role_name):
        """查询提示库里面的人设内容
        参数： role_name ： 人设名称
        返回值：如果读取成功返回读取值，否则返回False
        """
        role_name += ".txt"  # 补足后缀名
        path = os.path.join("用户设置/提示库/", role_name)
        if not os.path.isfile(path):  # 检查是否有这个文件（文件不存在）
            print("不存在该人设，无法进行打印")
            return False
        with open(path, "r", encoding="utf-8") as role_txt:
            role_content = role_txt.read()  # 必须临时保存，不然返回值无法处理
            print(f"人设内容:\n{role_content}")
        return f"人设内容:\n{role_content}"

    def print_role_content(self):
        """打印当前人设"""
        if self is None:    # 人设为空
            print("\033[91m当前人设为空\033[0m")  # 亮红色
            return False
        else:
            print(f"当前人设:{self.role}")
        return f"当前人设:{self.role}"

    def set_role(self, role_txt, out = False):
        """对人设属性进行修改
        参数： out : 修改成功是给提示，默认False
        返回值：
        """
        if not role_txt:    # 自定义人设为空
            print("\033[91m自定义人设内容为空\033[0m")
            return False
        self.role = role_txt
        if len(self.dialog_history) == 0:       # 没有任何对话记录，对开头进行人设添加
            self.dialog_history.append({"role": "system", "content": self.role})
        elif len(self.dialog_history) > 0:  # 存在对话记录不确定有没有之前的人设
            if self.dialog_history[0]["role"] == "system":  # 设置了人设
                self.dialog_history[0] = {"role": "system", "content": self.role}   # 把之前的人设替换掉
            else:   # 在消息头插入人设
                self.dialog_history.insert(0,{"role": "system", "content": self.role})
        if out: print("自定义人设成功")
        return True

    def remove_role(self, out = False):
        """删除人设
        参数 ： out ： 是否输出修改成功或失败,默认False
        返回值：修改成功返回True，否则返回False
        """
        if len(self.dialog_history) == 0:  # 没有任何消息头，即没有设置人设
            if out: print("\033[91m未设置人设，不需要进行删除\033[0m")
            return False
        elif len(self.dialog_history) > 0: # 存在对话记录，需要进一步确认是否有人设
            if self.dialog_history[0]["role"] == "system":  # 设置了人设
                self.dialog_history.pop(0)  # 删除第一个元素(人设)
                if out: print("成功删除人设")
                return True
            else:
                if out: print("\033[91m未设置人设，不需要进行删除\033[0m")
        return False    # 显式调用

    def scene_switch(self, scene_key, out = False):
        """9大场景切换，输入关键字自动调整合适参数（）
        温度调控借鉴:代码生成 / 数学解题(0.0)、数据抽取 / 分析(1.0)、通用对话(1.3)、翻译(1.3)、创意类写作 / 诗歌创作(1.5)
        参数： scene_key ： 字符串(代码、数学、数据、分析、对话、翻译、创作、写作、作诗)
        out ： 是否在屏幕上打印
        返回值：字符串，已切换至..模式
        """
        scene = {"代码": ["deepseek-reasoner", False, 0.0, 0.8, 0.4],
                 "数学": ["deepseek-reasoner", False, 0.0, 0.5, 0.6],
                 "数据": ["deepseek-reasoner", False, 1.0, 0.7, 0.5],
                 "分析": ["deepseek-reasoner", False, 1.0 ,0.6, 0.7],
                 "对话": ["deepseek-chat", True, 1.3, 0.4, 0.2],
                 "翻译": ["deepseek-chat", True, 1.3, 0.3, 0.3],
                 "创作": ["deepseek-reasoner", False, 1.5, 0.9, 0.1],
                 "写作": ["deepseek-reasoner", False, 1.5, 0.9, 0.1],
                 "作诗": ["deepseek-reasoner", False, 1.5, 1.2, -0.2]}
        self.max_tokens = 8192  # 设置最大token数为最大值
        self.model_choice = scene[scene_key][0]     # 模型选择
        self.stream = scene[scene_key][1]           # 是否开启流式输出
        self.temperature = scene[scene_key][2]      # 温度调控
        self.frequency_penalty = scene[scene_key][3]# 重复抑制系数(频次惩罚系数)
        self.presence_penalty = scene[scene_key][4] # 内容创新系数(存在惩罚系数)
        if out: print(f"已切换至{scene_key}场景")
        return  f"已切换至{scene_key}场景"

    def conversation_engine(self, text):
        """对话引擎
        参数： text ： 文本（问题或指令）
        """
        if self.quick_order(text):   # 字典查找函数
            print(end="")   # 不进行任何操作(减少在执行了字典后还多进行一次判断)
        elif text == "#FIM补全":
            self.set_prompt(input("请输入需要补全的开头:"),False) # 不输出
            self.set_suffix(input("请输入需要补全的后缀(可以不填):"),False)   # 不输出
            self.fill_in_the_middle_ask()
        else:
            self.ask(text,True) # 进行提问并将结果打印出来
        self.dialog_history_manage()  # 自动管理之前的对话历史

    """余额计算和监控"""
    def balance_inquiry(self, out = False):
        """查询deepseek的API余额
        参数：
        DEEPSEEK_API_KEY ： API密钥
        out : 是否对返回值进行打印
        返回值：返回一个列表
        0 ： 布尔值（余额是否充足）
        1 ： 字符串型（货币类型）
        2 : 字符串型（总的可用余额(包括赠金和充值余额)）
        3 ： 未过期的赠金余额
        4 ： 充值余额
        """
        return_list = list()  # 返回值的列表
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.__DEEPSEEK_API_KEY}'  # 密钥
        }
        response = requests.request("GET", self.balance_inquiry_url, headers=headers, data={})  # 发送查询请求
        data = json.loads(response.text)  # 解析json数据，(必须使用json库，本身就是文本格式和避免陷阱)
        if data["is_available"]:  # 如果为True
            return_list.append(True)
            if out: print("\033[92m余额充足，api可以调用\033[0m", end="\t")
        elif not data["is_available"]:  # 如果为False
            return_list.append(False)
            if out: print("\033[91m余额不足，api无法调用\033[0m", end="\t")
        detail_list = data["balance_infos"]  # 详细信息
        currency_type = ""  # 货币类型放置
        if detail_list[0]["currency"] == "CNY":  # 人民币
            return_list.append("元")
            currency_type = "元"  # 货币类型为人民币
        elif detail_list[0]["currency"] == "USD":  # 美元
            return_list.append("美元")
            currency_type = "美元"  # 货币类型为美元
        return_list.append(detail_list[0]["total_balance"])
        return_list.append(detail_list[0]["granted_balance"])
        return_list.append(detail_list[0]["topped_up_balance"])
        if out:
            print(f"总的可用余额(包括赠金和充值余额):{detail_list[0]["total_balance"]}{currency_type}", end="\t")
            print(f"未过期的赠金余额:{detail_list[0]["granted_balance"]}{currency_type}", end="\t")
            print(f"充值余额:{detail_list[0]["topped_up_balance"]}{currency_type}")
        return return_list

    def calculate_token_capacity(self, out = False):
        """计算余额可用token和字数
        参数：
        DEEPSEEK_API_KEY ： API密钥
        out : 是否对返回值进行打印
        返回值：返回一个列表
        min_token : 可用token数
        characters ： 最少的中文字符字数(直接取整数)
        words ： 最少的英文字符字数(直接取整数)
        round(((characters*24)/1024)/1024,2)  ： 最少可生产的数据(GB)
        round(characters/880000,2)  : 约几本《三体》(88万字一本)
        """
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.__DEEPSEEK_API_KEY}'  # 密钥
        }
        response = requests.request("GET", self.balance_inquiry_url, headers=headers, data={})  # 发送查询请求
        data = json.loads(response.text)  # 解析json数据，(必须使用json库，本身就是文本格式和避免陷阱)
        detail_list = data["balance_infos"]  # 详细信息
        min_token = float(detail_list[0]["total_balance"]) * 62500  # 当前金额(元) * 62500[每元的token数]
        characters = int(min_token / 0.6)  # 最少的中文字符字数(直接取整数)
        words = int(min_token / 0.3)  # 最少的英文字符字数(直接取整数)
        if out:
            print(
                f"当前可用余额能生成最少 {int(min_token)} token，对话可使用最少约{characters}个汉字，对话可使用最少约{words}英文字符")
            print(
                f"最少可生产:{round(((characters * 24) / 1024) / 1024, 2)}GB 的对话数据， 约{round(characters / 880000, 2)}本《三体》(88万字一本)")
        return int(min_token), characters, words, round(((characters * 24) / 1024) / 1024, 2), round(characters / 880000, 2)

    def return_balance(self):
        """输出余额（简化不必要的参数，仅提取常用有效返回值组成字符串）
        返回值：字符串
        """
        detail_list = self.balance_inquiry(True)
        return f"DeepSeek API余额：{detail_list[2]}{detail_list[1]}"

    def return_token(self):
        """量化可用token和字数（简化不必要的参数，仅提取常用有效返回值组成字符串）
        返回值：字符串
        """
        min_token, characters, words, data, books = self.calculate_token_capacity(True)
        text = f"""当前可用余额能生成最少 {min_token} token，对话可使用最少约{characters}个汉字，对话可使用最少约{words}英文字符，最少可生产:{data}GB 的对话数据， 约{books}本《三体》(88万字一本)"""
        return text

    """Token分词和计算"""
    def calculate_token(self, input_text, out = False):
        """计算总的token数
        参数：
        input_text ： 需要计算token的文本
        out ： 默认为False，是否输出过程信息
        返回值：输入文本的token数
        """
        # add_special_tokens=False标记仅编码原始文本内容纯文本Token计算
        result = self.tokenizer.encode(input_text, add_special_tokens=False)
        if out:
            print(f"输入的文本：{input_text}")
            # print(tokenizer.convert_ids_to_tokens([30594, 303, 3427, 3])) # 转义回去
            print(f"Token 数量: {len(result)}")
        return len(result)

    def token_ids(self, input_text, out = False):
        """使用分词器将符号转换为ID
        参数：
        input_text  ： 需要转为ID的文本
        out ： 默认为False，是否输出过程信息
        返回值：字符ID序列组
        """
        result = self.tokenizer.encode(input_text, add_special_tokens=False)
        if out:
            print(f"输入的文本：{input_text}")
            print(f"字符ID序列组: {result}")
        return result

    def restore_text(self, input_text, out = False):
        """token分词转文本
        参数：
        input_text ： 一个包含 token ID 的列表（数组类型）
        out ： 默认为False，是否输出过程信息
        返回值：文本
        """
        # print(tokenizer.decode([30594, 303, 3427, 3])) # 转义回去
        result = self.tokenizer.decode(input_text)
        if out:
            print(f"输入token ID 的列表：{input_text}")
            print(f"还原的文本:{result}")
        return result

    """快捷指令"""
    def quick_order(self, order):
        """快捷指令（调用此方法后可通过关键字快速找到其他方法）
        参数： order ： 字符串(设置的指令)
        返回值：如果指令存在则执行对应的函数后返回True，如果指令不存在返回False
        """
        # 函数映射表(使用lambda来匿名函数)
        function_map = {
            # 特殊指令
            "#兼容": lambda : self.compatible_openai(True),
            "#测试接口": lambda: self.use_beat(True),
            "#初始化": lambda: self.reset(True),  # 恢复最开始设置的参数（创建对象时的默认参数）
            # 对话参数调节指令
            "#模型切换": lambda : self.switch_model(True),
            "#V3模型": lambda: self.set_model("V3", True),
            "#R1模型" : lambda : self.set_model("R1", True),
            "#评分": lambda : self.score_answer(int(input("对此次回答进行评分(0-100分,默认50分):")),True),
            "#最大token数": lambda : self.set_max_tokens(int(input("请输入最大token限制(1-8192,默认4096):")),True),
            "#输出格式": lambda : self.set_response_format(input("请输入指定输出格式(text或json_object):"),True),
            "#敏感词": lambda : self.set_stop(input("设置敏感词:"),True),
            "#删除敏感词": lambda: self.del_stop(input("请输入需要删除的敏感词:"),True),
            "#流式": lambda : self.set_stream(True,True),
            "#非流式": lambda : self.set_stream(False,True),
            "#开启请求统计": lambda : self.set_stream_options(True if input("请输入 True 或 None :")== "True" else None,True),
            "#关闭请求统计": lambda : self.set_stream_options(None,True),
            "#温度": lambda : self.set_temperature(float(input("请输入温度,数值越小全文逻越严谨(0.0-2.0,默认1.0):")),True),
            "#核采样": lambda : self.set_top_p(float(input("请输入核采样,数值越小内容部分逻越严谨(0.0-1.0,默认1.0):")),True),
            "#工具列表": lambda : self.set_tools(input("请输入模型可能会调用的 tool 的列表(默认为None):"),True),
            "#工具开关": lambda : self.switch_tool_choice(True),
            "#开启对数概率输出": lambda : self.set_logprobs(True,True),
            "#关闭对数概率输出": lambda : self.set_logprobs(False,True),
            "#位置输出概率": lambda : self.set_top_logprobs(int(input("请指定的每个输出位置返回输出概率top为几的token(0-20，默尔为None):")),True),
            # FIM对话参数
            "#FIM对话": lambda : self.fill_in_the_middle_ask(),   # 使用FIM对话补全
            "#FIM补全开头": lambda : self.set_prompt(input("请输入需要补全的开头:")),
            "#FIM完整输出": lambda : self.set_echo(False,True),    # 这个参数就只有False和None了，改不了一点
            "#FIM对数概率输出": lambda : self.set_FIM_logprobs(int(input("请输入需要多少个候选token数量输出对数概率(0-20,默认0):")),True),
            "#FIM补全后缀": lambda : self.set_suffix(input("请输入需要补全的后缀(可以不填):")),
            # 上下文参数
            "#思维链": lambda : self.reasoning_content_output(True),
            "#对话轮次": lambda : self.set_dialog_history(int(input("请输入最大对话轮数(超过自动删除):")),True),
            "#聊天记录": lambda : self.print_dialog_history(True),
            "#清空对话历史": lambda : self.clear_dialog_history(True),
            # 多人设管理
            "#人设切换": lambda: self.role_switch(input("请输入切换的人设:")),
            "#所有人设": lambda : self.role_list(True),
            "#人设查询": lambda : self.select_role_content(input("请输入要查询的人设:")),
            "#当前人设": lambda : self.print_role_content(),
            "#人设自定": lambda : self.set_role(input("请输入人设内容:")),
            "#删除人设": lambda : self.remove_role(True),
            # 场景关键词自动调控参数
            "#代码": lambda : self.scene_switch("代码",True),
            "#数学": lambda : self.scene_switch("数学",True),
            "#数据": lambda : self.scene_switch("数据",True),
            "#分析": lambda : self.scene_switch("分析",True),
            "#对话": lambda : self.scene_switch("对话",True),
            "#翻译": lambda : self.scene_switch("翻译",True),
            "#创作": lambda : self.scene_switch("创作",True),
            "#写作": lambda : self.scene_switch("写作",True),
            "#作诗": lambda : self.scene_switch("作诗",True),
            # 余额和token数查询
            "#余额": lambda : self.return_balance(),
            "#token": lambda : self.return_token()
        }
        if order in function_map:   # 检查指令是否在函数映射字典中
            function = function_map[order]  # 拿到映射的函数
            function()  # 执行映射的函数
            return True
        return False    # 没有拿到映射函数就返回

    def quick_order_api(self, order: str):
        """快捷指令api（调用此方法后自动分割后通过关键字快速找到其他方法）
        参数： order ： 收到的消息(#R1 模型)
        返回值：如果指令存在则执行对应的函数后返回反应值，如果指令不存在返回False
        """
        respond = ""    # 用来接收回应值(提示是否需改成功)
        # 用来放置参数(必须存在,需要用来判断是否需要参数)
        args = None
        # 函数映射表(使用lambda来匿名函数)，直接把指点放到环境变量外，防止每次加载的时候都是
        function_map = {
            # 特殊指令
            "#兼容": [lambda: self.compatible_openai(), "已经切换至兼容OpenAI的接口", "切换中途发生异常"],
            "#测试接口": [lambda: self.use_beat(), "已切换至测试接口", "切换中途发生异常"],
            "#初始化": [lambda: self.reset(), "已格式化deepseek对话引擎", "初始化中途发生异常"],
            # 恢复最开始设置的参数（创建对象时的默认参数）
            # 对话参数调节指令
            "#模型切换": [lambda: self.switch_model(True),
                          lambda: "已切换至V3模型" if self.model_choice == "deepseek-chat" else "已切换至R1模型",
                          "切换中途发生异常"],
            "#V3模型": [lambda: self.set_model("V3"), "已切换至V3模型", "切换中途发生异常"],
            "#R1模型": [lambda: self.set_model("R1"), "已切换至R1模型", "切换中途发生异常"],
            "#评分": [lambda score=50: self.score_answer(score), "评分成功", "超出打分范围([0-100]分,默认50分)"],
            "#最大token数": [lambda max_tokens=4096: self.set_max_tokens(max_tokens),
                             lambda: f"已修改最大token数为{self.max_tokens}",
                             "超出最大token数范围([1-8192]分,默认4096)"],
            "#输出格式": [lambda response_format: self.set_response_format(response_format),
                          lambda: f"已修改为{self.response_format}格式",
                          "格式有误，指定模型必须输出的格式为\"text\"或\"json\""],
            # input("请输入指定输出格式(text或json,],默认text):")
            "#敏感词": [lambda stop: self.set_stop(stop), lambda: f"添加敏感词 {args} 成功", "添加失败"],
            # input("设置敏感词(默认为None):")
            "#删除敏感词": [lambda stop: self.del_stop(stop), "删除成功", "敏感词不存在"],
            "#流式": [lambda: self.set_stream(True), "已切换至流式输出", "切换中途发生异常"],
            "#非流式": [lambda: self.set_stream(), "已切换至流式输出", "切换中途发生异常"],
            "#开启请求统计": [lambda: self.set_stream_options(True), "已开启请求统计",
                              "必须先开启流式(stream)才能开启修改开启这个字段"],
            "#关闭请求统计": [lambda: self.set_stream_options(), "已关闭请求统计", "关闭请求统计途中发生异常"],
            "#温度": [lambda temperature: self.set_temperature(temperature),
                      lambda: f"已修改温度为{self.temperature}", "超出温度范围([0.0-2.0,]默认1.0)"],
            "#核采样": [lambda top_p: self.set_top_p(top_p), lambda: f"已修改核采样为{self.top_p}",
                        "超出核采样范围([0.0-1.0]分,默认1.0)"],
            # float(input("请输入核采样,],数值越小内容部分逻越严谨(0.0-1.0,],默认1.0):"))
            "#工具列表": [lambda: self.set_tools(), "修改成功", "修改未成功"],
            # input("请输入模型可能会调用的 tool 的列表(默认为None):")
            "#工具开关": [lambda: self.switch_tool_choice(), "已开启工具调用", "已关闭工具调用"],
            "#开启对数概率输出": [lambda: self.set_logprobs(True), "已开启对数概率输出", "开启对数概率失败"],
            "#关闭对数概率输出": [lambda: self.set_logprobs, "已关闭对数概率输出", "关闭对数概率失败"],
            "#位置输出概率": [lambda top_logprobs: self.set_top_logprobs(top_logprobs),
                              lambda: f"已修改概率输出个数为{self.top_logprobs}",
                              "未开启对数概率输出或参数不在调用范围(0-20)"],
            # int(input("请指定的每个输出位置返回输出概率top为几的token(0-20，默尔为None):"))
            # FIM对话参数
            "#FIM对话": [True, lambda: self.fill_in_the_middle_ask(), "调用失败"],  # 使用FIM对话补全
            "#FIM补全开头": [lambda prompt: self.set_prompt(prompt), "已补全开头", "补全开头失败"],
            "#FIM完整输出": [lambda: self.set_echo(), "因为服务器那边不接受True，只接受False和None,所以这个功能无效",
                             "因为服务器那边不接受True，只接受False和None,所以这个功能无效"],  # 这个参数就只有False和None了，改不了一点
            "#FIM对数概率输出": [lambda FIM_logprobs: self.set_FIM_logprobs(FIM_logprobs),
                                 lambda: f"已制定输出中保留{self.FIM_logprobs}个最可能输出token的对数概率",
                                 "参数不在调用范围[0-20]"],  # int(input("请输入需要多少个候选token数量输出对数概率(默认0):"))
            "#FIM补全后缀": [lambda suffix: self.set_suffix(suffix), "已补全后缀", "后缀补全失败"],
            # input("请输入需要补全的后缀(默认为None):")
            # 上下文参数
            "#思维链": [lambda: self.reasoning_content_output(), lambda: self.reasoning_content, "思维链为空"],
            # 会返回False或字符串
            "#对话轮次": [lambda dialog_round: self.set_dialog_history(dialog_round),
                          lambda: "已解除对话轮次限制，注意最大token数和高额消费" if self.clear_flag == -1 else f"已设置对话轮次为{self.clear_flag}轮",
                          "无法设置对话轮次为负数"],  # int(input("请输入最大对话轮数，超过自动删除(默认值为5):"))
            "#聊天记录": [lambda: self.print_dialog_history(), lambda: "\n".join(self.print_dialog_history()),
                          "聊天记录为空"],
            "#清空对话历史": [lambda: self.clear_dialog_history(), "已清空对话历史(人设除外)",
                              "对话历史为空无需清空"],
            # 多人设管理
            "#人设切换": [lambda role_name: self.role_switch(role_name), lambda: f"已切换人设为：{args}",
                          "提示库不存在该人设"],  # input("请输入切换的人设:")
            "#所有人设": [lambda: self.role_list(), lambda: "提示库的所有人设:" + "、".join(self.role_list()),
                          "提示库中为空，不存在任何人设"],  # 人设做了处理
            "#人设查询": [lambda role_name: self.select_role_content(role_name),
                          lambda: self.select_role_content(args), "不存在该人设，无法进行打印"],
            # input("请输入要查询的人设:")
            "#当前人设": [lambda: self.print_role_content(), lambda: f"当前人设:{self.role}", "当前人设为空"],
            "#人设自定": [lambda role_txt: self.set_role(role_txt), "自定义人设成功", "自定义人设失败"],
            # input("请输入人设内容:")
            "#删除人设": [lambda: self.remove_role(), "成功删除人设", "未设置人设，不需要进行删除"],
            # 场景关键词自动调控参数
            "#代码": [lambda: self.scene_switch("代码"), "已切换至代码场景", "切换场景失败"],
            "#数学": [lambda: self.scene_switch("代码"), "已切换至数学场景", "切换场景失败"],
            "#数据": [lambda: self.scene_switch("数据"), "已切换至数据场景", "切换场景失败"],
            "#分析": [lambda: self.scene_switch("分析"), "已切换至分析场景", "切换场景失败"],
            "#对话": [lambda: self.scene_switch("对话"), "已切换至对话场景", "切换场景失败"],
            "#翻译": [lambda: self.scene_switch("翻译"), "已切换至翻译场景", "切换场景失败"],
            "#创作": [lambda: self.scene_switch("创作"), "已切换至创作场景", "切换场景失败"],
            "#写作": [lambda: self.scene_switch("写作"), "已切换至写作场景", "切换场景失败"],
            "#作诗": [lambda: self.scene_switch("作诗"), "已切换至作诗场景", "切换场景失败"],
            # 余额和token数查询
            "#余额": [True, lambda: self.return_balance(), "无法查询"],
            "#token": [True, lambda: self.return_token(), lambda: self.return_balance(), "无法查询"]
        }
        def execute_function(true_false_result):
            """是否执行返回值的函数
            参数 : true_false_result  ；执行结果
            """
            nonlocal respond    # 确定respond是函数的值(确定作用域)
            if true_false_result:  # 执行结果有效果
                if function_check(function_map[order][1]):  # 真值是一个函数
                    respond = function_map[order][1]()  # 执行真值的函数并发送
                else:
                    respond = function_map[order][1] # 直接发送真值
            else:
                if function_check(function_map[order][2]):  # 假值是一个函数
                    respond = function_map[order][2]()  # 执行假值的函数并发送
                else:
                    respond = function_map[order][2]  # 直接发送假值

        function_check = lambda def_function: True if isinstance(def_function, (types.LambdaType, types.FunctionType,
                                                                                types.MethodType)) else False  # 检查是否为匿名函数
        # 检查指令是否包含参数并做处理
        if ":" in order:  # 如何指令中存在:代表的是参数
            if not order.split(":", 1)[1]:  # 参数为空
                respond = "参数为空"  # 有:却不填
                return False, respond
            order, args = order.split(":", 1)[0], order.split(":", 1)[1]  # 分割指令和参数
        # 检查指令是否在函数映射字典中
        if order not in function_map:  # 指令不在字典里面
            respond = "不存在该指令"
            print("\033[93m接收到了不存在的指令\033[0m")
            return False, respond  # 没有这个指令
        else:
            if function_check(function_map[order][0]) and args is None:  # 是一个无参函数
                print("\033[92m无参函数执行了\033[0m")
                try:  # 假设没有:却必须要填入参数没有填
                    result = function_map[order][0]()  # 执行函数并拿到返回结果
                    execute_function(result)
                except TypeError:
                    if function_check(function_map[order][2]):  # 假值是一个函数
                        respond = "请在指令中附带必要参数:\n" + function_map[order][2]()  # 执行假值的函数并发送
                    else:
                        respond = "请在指令中附带必要参数:\n" + function_map[order][2]  # 直接发送假值
            elif function_check(function_map[order][0]) and args is not None:  # 是有参函数
                print("\033[92m有参函数执行了\033[0m")
                result = function_map[order][0](args)  # 传入参数并执行函数并拿到返回结果
                execute_function(result)
            else:  # 不是一个函数(可能是None、True、False)
                print("\033[92m不是函数执行了\033[0m")
                result = function_map[order][0]  # 传入的不是一个函数不执行，仅仅拿到值
                execute_function(result)
        return True, respond  # 存在指令且执行即返回True


if __name__ == '__main__':
    deepseek = DeepseekConversationEngine()  # 实例化对象(设置人设为专属猫娘)
    deepseek.set_stream(True)  # 设置流式输出
    while True:
        content = input("我：")
        if content == "#退出": break  # 退出循环调用对话的指令
        deepseek.conversation_engine(content)  # 调用对话引擎
    print("已退出对话引擎的调用")
    # text = """"
    # 你好
    # """
    # deepseek.set_model("R1", True)
    # deepseek.set_temperature(0.0, True)
    # deepseek.ask(text, True)
    # deepseek.reasoning_content_output(True)


