import json
import os


class SpecInfo:
    """ 存储协议相关信息 """

    def __init__(self, arguments):
        # 读取协议名称和目录
        self.spec = arguments["spec"]
        self.spec_name = os.path.split(self.spec)[1]

        # 读取协议配置文件
        spec_config_file = os.path.join(self.spec) + ".config.json"
        spec_config = json.load(open(spec_config_file))

        # 从配置文件中读取具体参数
        self.relations = spec_config["relations"]
        self.safety = spec_config["safety"]
        self.next = spec_config["next"]
        self.constants = spec_config["constants"]

        self.type_ok = spec_config["type_ok"]
        self.sort_value = spec_config["sort_value"]
        self.const_sort = spec_config["const_sort"]
        self.init = spec_config["init"]
