from spec_info import SpecInfo

# 生成的Ivy关系前缀
relation_prefix_word = "Rel"
# 生成的TLA关系中分隔常量的分隔符
relation_const_sep = "__"


# 自动生成Ivy关系名
def generate_name():
    return relation_prefix_word + str(TLARelDict.rel_count_getter())


# 根据序号获取Ivy关系名
def get_rel_name(index):
    return relation_prefix_word + str(index)


def get_rel_name_arg(name: str):
    return name.split(relation_const_sep)


class TLARelDict:
    # 目前关系序号
    __rel_count = -1

    def __init__(self, spec_info: SpecInfo):
        tla_preds = spec_info.relations
        self.rel_dict = {}
        self.rel_list = []
        # 常量替换后的TLA+关系名：常量替换后的TLA+表达式
        self.rel_dict_substituted = {}
        self.spec_info = spec_info
        for p in tla_preds:
            self.rel_dict[p] = generate_name()
            self.rel_list.append(p)

        # 为rel中的每个关系生成常量替换后的对应项
        def substitute(rel: dict, constant, sort):
            result = {}
            for n, r in rel.items():
                find_pos = r.find(constant)
                if find_pos != -1:
                    for sort_value in self.spec_info.sort_value[sort]:
                        temp = r.replace(constant, '\"' + sort_value + '\"')
                        new_name = n + relation_const_sep + sort_value
                        result[new_name] = temp
                else:
                    return rel
            return result

        for i in range(len(self.rel_list)):
            temp_dict = {}
            for c, s in self.spec_info.const_sort.items():
                if len(temp_dict) == 0:
                    rel_name = get_rel_name(i)
                    temp_dict[rel_name] = self.get_tla_rel_by_name(rel_name)
                temp_dict = substitute(temp_dict, c, s)
            for name, sub_rel in temp_dict.items():
                self.rel_dict_substituted[name] = sub_rel

    # 根据TLA+表达式获取Ivy关系名
    def get_tla_rel_name_by_exp(self, rel: str):
        if rel in self.rel_dict:
            return self.rel_dict[rel]
        else:
            return None

    # 根据Ivy关系名获取TLA+表达式
    def get_tla_rel_by_name(self, rel: str):
        if rel.startswith(relation_prefix_word):
            num = int(rel[len(relation_prefix_word):])
            if len(self.rel_list) > num >= 0:
                return self.rel_list[num]
        else:
            return None

    def get_rels(self):
        return self.rel_list

    # 返回Ivy关系名列表
    def get_rel_names(self):
        rel_names = []
        for i in range(len(self.rel_list)):
            rel_names.append(get_rel_name(i))
        return rel_names

    def get_rel_list(self):
        return self.rel_list

    # 获取常量替换后的TLA+关系名和表达式
    def get_substituted_rels(self):
        return self.rel_dict_substituted

    # 根据带有常量名的TLA+关系名生成Ivy关系
    def get_substituted_rel(self, name: str):
        name_arg = get_rel_name_arg(name)
        if len(name_arg) == 1:
            return
        rel = self.get_tla_rel_by_name(name_arg[0])
        i = 1
        while i <= len(name_arg):
            for c in self.spec_info.const_sort.keys():
                if rel.find(c) != -1:
                    rel.replace(c, name_arg[i], 1)
                    i += 1
                    break
        return rel

    # 获取TLA表达式中出现过的常量
    def get_rel_args(self, rel: str):
        result = []
        for c in self.spec_info.const_sort.keys():
            if rel.find(c) != -1:
                result.append(c)
        return result

    def get_var_sort(self, var: str):
        if var in self.spec_info.const_sort.keys():
            return self.spec_info.const_sort[var]
        else:
            return None

    @classmethod
    def rel_count_getter(cls):
        cls.__rel_count += 1
        return cls.__rel_count
