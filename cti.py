import random

import apalache_utils
import structure
import tla_rel_dict
from folseparators import separators
from rel_checker import RelChecker
from spec_info import SpecInfo
from file_utils import write_gen_tla
from tla_rel_dict import TLARelDict


class CTI:
    """ 表示一个CTI状态 """

    def __init__(self, cti_str, spec: SpecInfo, frame_predicates, rel_dict: TLARelDict):
        self.cti_str = cti_str
        self.spec_info = spec
        self.frame_predicates = frame_predicates
        self.rel_dict = rel_dict
        self.rel_value = []
        self.ivy_state = None
        self.generated_file_name = ''

    def get_cti_state_string(self):
        return self.cti_str

    def find_predecessor(self, frame_predicates):
        # 生成随机数代表此次生成，避免命名冲突
        tag = random.randint(0, 10000)
        cti_seed = random.randint(0, 10000)

        # 生成寻找前继状态所需的TLA文件
        # 生成协议头
        predecessor_tla = f"---- MODULE {self.spec_info.spec_name}_Predecessor_{cti_seed} ----\n"
        predecessor_tla += "EXTENDS %s, Apalache\n\n" % self.spec_info.spec_name
        cti_state = "not_State0 ==\n" + str(structure.TLANot(self.cti_str))
        predecessor_tla += cti_state
        # 将TypeOK和当前CTI代表的状态（未来需要加入frame_predicates)加入归纳不变式中
        ind_inv_list = [structure.TLAUnresolved(self.spec_info.type_ok), structure.TLAAnd(frame_predicates)]
        ind_inv = str(structure.TLAAnd(ind_inv_list))
        predecessor_tla += "InvForPredSearch ==\n"
        predecessor_tla += ind_inv + "\n"
        predecessor_tla += "===="

        predecessor_file = f"{self.spec_info.spec_name}_Predecessor_{cti_seed}.tla"
        write_gen_tla(predecessor_file, predecessor_tla)

        # 清空反例生成目录.
        # os.system("rm -f benchmarks/gen_tla/apalache-cti-out/*")

        result = apalache_utils.apalache_check('apalache-cti-out', 'InvForPredSearch', 'not_State0',
                                               1, predecessor_file)
        file_content = apalache_utils.check_get_file(result)
        state_str = apalache_utils.get_state(file_content, 0)
        if state_str is None:
            return None
        state = CTI(state_str, self.spec_info, self.frame_predicates, self.rel_dict)

        return state

    def generate_cti_file(self):
        if self.generated_file_name != '':
            return self.generated_file_name
        cti_seed = random.randint(0, 10000)

        # 生成寻找前继状态所需的TLA文件
        # 生成协议头
        cti_tla = f"---- MODULE {self.spec_info.spec_name}_CTI_{cti_seed} ----\n"
        cti_tla += f"EXTENDS {self.spec_info.spec_name}, Apalache, {self.spec_info.spec_name}_RelCheck\n\n"
        cti_state = "State0 ==\n" + self.cti_str
        cti_tla += cti_state
        cti_tla += "===="

        cti_file = f"{self.spec_info.spec_name}_CTI_{cti_seed}.tla"
        write_gen_tla(cti_file, cti_tla)
        self.generated_file_name = cti_file
        return cti_file

    def get_rel_value(self):
        if len(self.rel_value) == 0:
            cti_file = self.generate_cti_file()
            checker = RelChecker(self.rel_dict, self.spec_info)
            self.rel_value = checker.check_rel(cti_file)
        return self.rel_value

    def get_ivy_state(self, sig):
        if self.ivy_state is not None:
            return self.ivy_state
        m = separators.logic.Model(sig)
        for k, v in self.spec_info.sort_value.items():
            for detailed in v:
                m.add_elem(detailed, k)
        subs = self.rel_dict.get_substituted_rels()
        vals = self.get_rel_value()
        z = list(zip(subs, vals))
        for r, v in z:
            name_arg = tla_rel_dict.get_rel_name_arg(r)
            if v:
                m.add_relation(name_arg[0], name_arg[1:])
        self.ivy_state = m
        return m

    def __hash__(self):
        return hash(self.cti_str)

    def __eq__(self, other):
        return hash(self.cti_str) == hash(other.cti_str)

    def __str__(self):
        return self.cti_str

    # Order CTIs as strings.
    def __lt__(self, other):
        return self.cti_str < other.cti_str
