import apalache_utils
import tla_rel_dict
from tla_rel_dict import TLARelDict
from spec_info import SpecInfo
from file_utils import write_gen_tla
from apalache_utils import apalache_check


class RelChecker:

    def __init__(self, rel_dict: TLARelDict, spec_info: SpecInfo):
        self.dict = rel_dict
        self.spec_info = spec_info
        self.generate_rel_file()

    def generate_rel_file(self):
        rel_check_tla = f"---- MODULE {self.spec_info.spec_name}_RelCheck ----\n"
        rel_check_tla += f"EXTENDS {self.spec_info.spec_name}, Apalache\n\n"
        # rel_list = self.dict.get_rels()

        for name, sub_rel in self.dict.rel_dict_substituted.items():
            rel_check_tla += f"{name} == {sub_rel}\n"

        rel_check_tla += "====\n"

        rel_check_tla_file_name = f"{self.spec_info.spec_name}_RelCheck.tla"
        write_gen_tla(rel_check_tla_file_name, rel_check_tla)
        return rel_check_tla_file_name

    def check_rel(self, cti_file):
        output = apalache_check("rel_check", "State0", list(self.dict.get_substituted_rels().keys()), 0, cti_file)
        result = []
        for o in output:
            result.append(apalache_utils.get_value(o))
        return result

    def generate_initial_file(self):
        initial_generate_tla = f"---- MODULE {self.spec_info.spec_name}_InitialGenerate ----\n"
        initial_generate_tla += f"EXTENDS {self.spec_info.spec_name}, Apalache\n\n"

        prev_names = []
        for name, sub_rel in self.dict.rel_dict_substituted.items():
            name_arg = tla_rel_dict.get_rel_name_arg(name)
            if name_arg[0] not in prev_names:
                initial_generate_tla += f"{name_arg[0]} == {sub_rel}\n"
                prev_names.append(name_arg[0])

        initial_generate_tla += "====\n"

        initial_check_tla_file_name = f"{self.spec_info.spec_name}_InitialGenerate.tla"
        write_gen_tla(initial_check_tla_file_name, initial_generate_tla)
        return initial_check_tla_file_name

    def check_initial(self, initial_file):
        output = apalache_check("rel_check", self.spec_info.init, self.dict.get_rel_names(), 0, initial_file)
        result = []
        for o in output:
            result.append(apalache_utils.get_value(o))
        return result
