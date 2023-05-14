import apalache_utils
import structure
from apalache_utils import apalache_check, get_state
from cti import CTI
from file_utils import write_gen_tla
from fol_separator import FOLSeparator
from structure import *
from rel_checker import RelChecker


class IC3:
    def __init__(self, tla_dict: TLARelDict, spec_info: SpecInfo):
        self.dict = tla_dict
        self.spec_info = spec_info
        self.predicates = []
        self.frame_numbers = []
        self.frame_n = 1
        self.transitions = []
        self.initial_states = []

    def fol_ic3(self):
        self.generate_init_preds()
        # self.predicates.append(TLAUnresolved(self.spec_info.safety))
        # self.frame_numbers.append(1)
        # safety_pos = len(self.frame_numbers)-1
        while True:
            self.push()
            pred_list = self.frame_predicates(self.frame_n)
            bad_state = self.check_safety(pred_list)
            if bad_state is not None:
                self.block(bad_state, self.frame_n)
            else:
                self.print_predicates()
                for inv_frame in reversed(range(1, self.frame_n + 1)):
                    if not any(inv_frame == f for f in self.frame_numbers):
                        continue
                    ps1 = self.frame_predicates(inv_frame)
                    ps1.insert(0, TLAUnresolved(self.spec_info.type_ok))
                    frame1 = TLAAnd(ps1)
                    ps2 = self.frame_predicates(inv_frame)
                    frame2 = TLAAnd(ps2)
                    if self.check_inductive(frame1, frame2) is None:
                        print(f"Found inductive invariant in frame {inv_frame}!")
                        for p in self.frame_predicates(inv_frame):
                            print(f"invariant {p}")
                        return
                # self.push()
                # self.frame_numbers[safety_pos] += 1
                self.frame_n += 1

    def add_initial(self, s: CTI):
        self.initial_states.append(s)

    def add_transition(self, pre, post):
        self.transitions.append((pre, post))

    def frame_predicates(self, i: int):
        return [p for p, f in zip(self.predicates, self.frame_numbers) if i <= f]

    def add_predicates_to_frame(self, p, f):
        for i in range(len(self.predicates)):
            if p == self.predicates[i]:
                self.frame_numbers[i] = max(self.frame_numbers[i], f)
                return i
        self.predicates.append(p)
        self.frame_numbers.append(f)

    def frame_transitions(self, frame: int):
        pred_indices = TLAAnd([p for p, f in zip(self.predicates, self.frame_numbers) if frame <= f])
        return [(a, b) for a, b in self.transitions if
                self.check_elimination(a, pred_indices)]

    def block(self, s: CTI, i: int):
        print(f"blocking state in {i}")
        if i == 0:
            raise RuntimeError("Protocol is UNSAFE!")  # this should exit more cleanly

        while True:
            predecessor = s.find_predecessor(self.frame_predicates(i - 1))
            if predecessor is None:
                break
            self.block(predecessor, i - 1)
            if self.check_elimination(s, TLAAnd(self.frame_predicates(i))):
                print(f"State blocked by pushed predicate")
                return
        self.inductive_generalize(s, i)

    def inductive_generalize(self, s: CTI, i: int):
        print("Inductive generalizing")
        separation_states = [s]
        pos = []
        imp = []
        for init in self.initial_states:
            pos.append(init)
            separation_states.append(init)
        for (pre, post) in self.frame_transitions(i - 1):
            imp.append((pre, post))
            separation_states.append(pre)
            separation_states.append(post)

        sep = FOLSeparator(separation_states, self.spec_info, self.dict)

        while True:
            p = sep.separate(pos=pos, neg=[s], imp=imp)
            if p is None:
                raise RuntimeError("couldn't separate in inductive_generalize()")
            state = self.check_initial(p)
            if state is not None:
                pos.append(state)
                separation_states.append(state)
                self.add_initial(state)
                continue
            pred_list = self.frame_predicates(i - 1)
            pred_list.append(p)
            pred_list.insert(0, TLAUnresolved(self.spec_info.type_ok))
            tr = self.check_inductive(structure.TLAAnd(pred_list), p)
            if tr is not None:
                (pre_st, post_st) = tr
                imp.append(tr)
                separation_states.append(pre_st)
                separation_states.append(post_st)
                self.add_transition(pre_st, post_st)
                continue
            print(f"Learned new predicate: {str(p)}")
            self.add_predicates_to_frame(p, i)
            self.push()
            return

    def push(self):
        for frame in range(self.frame_n):
            for i in range(len(self.frame_numbers)):
                if self.frame_numbers[i] == frame:
                    pred_list = self.frame_predicates(frame)
                    pred_list.insert(0, TLAUnresolved(self.spec_info.type_ok))
                    cex = self.check_inductive(TLAAnd(pred_list), self.predicates[i])
                    if cex is None:
                        self.frame_numbers[i] += 1

    def generate_init_preds(self):
        checker = RelChecker(self.dict, self.spec_info)
        initial_file = checker.generate_initial_file()
        values = checker.check_initial(initial_file)
        relations = self.dict.get_rel_names()
        for i in range(len(relations)):
            rs = self.dict.get_tla_rel_by_name(relations[i])
            args = self.dict.get_rel_args(rs)
            tla_vars = list(map(lambda x: TLAVar(x), args))
            r = TLARelation(relations[i], tla_vars, self.dict, self.spec_info)
            if not values[i]:
                r = TLANot(r)
            final_pred = r
            for v in reversed(tla_vars):
                final_pred = TLAForall(v, self.dict.get_var_sort(str(v)), final_pred)
            self.predicates.append(final_pred)
            self.frame_numbers.append(0)

    # 检查 init => p 是否成立
    def check_initial(self, p):
        initial_check_tla = f"---- MODULE {self.spec_info.spec_name}_InitialCheck ----\n"
        initial_check_tla += f"EXTENDS {self.spec_info.spec_name}, Apalache\n\n"
        initial_check_tla += "InvForInitialCheck ==\n"
        initial_check_tla += str(p) + "\n"
        initial_check_tla += "====\n"

        initial_check_tla_file_name = f"{self.spec_info.spec_name}_InitialCheck.tla"
        write_gen_tla(initial_check_tla_file_name, initial_check_tla)

        output = apalache_check('rel_check', self.spec_info.init, 'InvForInitialCheck', 0, initial_check_tla_file_name)
        file_content = apalache_utils.check_get_file(output)
        state_str = get_state(file_content, 0)
        if state_str is None:
            return None
        state = CTI(state_str, self.spec_info, self.frame_predicates, self.dict)
        return state

    # 检查 init /\ T => inv 是否成立
    def check_inductive(self, init, inv):
        inductive_check_tla = f"---- MODULE {self.spec_info.spec_name}_InductiveCheck ----\n"
        inductive_check_tla += f"EXTENDS {self.spec_info.spec_name}, Apalache\n\n"
        inductive_check_tla += "InductiveCheckInit ==\n"
        inductive_check_tla += str(init) + "\n"
        inductive_check_tla += "InvForInductiveCheck ==\n"
        inductive_check_tla += str(inv) + "\n"
        inductive_check_tla += "====\n"

        inductive_check_tla_file_name = f"{self.spec_info.spec_name}_InductiveCheck.tla"
        write_gen_tla(inductive_check_tla_file_name, inductive_check_tla)

        output = apalache_check('rel_check', 'InductiveCheckInit', 'InvForInductiveCheck', 1,
                                inductive_check_tla_file_name)
        file_content = apalache_utils.check_get_file(output)
        state_str1 = get_state(file_content, 0)
        if state_str1 is None:
            return None
        state1 = CTI(state_str1, self.spec_info, self.frame_predicates, self.dict)
        state_str2 = get_state(file_content, 1)
        if state_str2 is None:
            return None
        state2 = CTI(state_str2, self.spec_info, self.frame_predicates, self.dict)
        return state1, state2

    # 检查 s => ind_inv 是否成立
    def check_elimination(self, s: CTI, ind_inv):
        elimination_check_tla = f"---- MODULE {self.spec_info.spec_name}_EliminationCheck ----\n"
        elimination_check_tla += f"EXTENDS {self.spec_info.spec_name}, Apalache\n\n"
        cti_state = "State0 ==\n" + s.cti_str
        elimination_check_tla += cti_state
        elimination_check_tla += "InvForEliminationCheck ==\n"
        elimination_check_tla += str(ind_inv) + "\n"
        elimination_check_tla += "====\n"

        elimination_check_tla_file_name = f"{self.spec_info.spec_name}_EliminationCheck.tla"
        write_gen_tla(elimination_check_tla_file_name, elimination_check_tla)

        output = apalache_check('rel_check', 'State0', 'InvForEliminationCheck', 0, elimination_check_tla_file_name)
        return apalache_utils.get_value(output)

    # 检查 type_ok /\ pred_list => safety
    def check_safety(self, pred_list):
        pred_list.insert(0, TLAUnresolved(self.spec_info.type_ok))
        safety_check_tla = f"---- MODULE {self.spec_info.spec_name}_SafetyCheck ----\n"
        safety_check_tla += f"EXTENDS {self.spec_info.spec_name}, Apalache\n\n"
        ind_inv = str(structure.TLAAnd(pred_list))
        safety_check_tla += "InvForSafetyCheck ==\n"
        safety_check_tla += ind_inv + "\n"
        safety_check_tla += "====\n"

        safety_check_tla_file_name = f"{self.spec_info.spec_name}_SafetyCheck.tla"
        write_gen_tla(safety_check_tla_file_name, safety_check_tla)

        output = apalache_check('rel_check', "InvForSafetyCheck", self.spec_info.safety, 0, safety_check_tla_file_name)
        file_content = apalache_utils.check_get_file(output)
        state_str = get_state(file_content, 0)
        if state_str is None:
            return None
        state = CTI(state_str, self.spec_info, self.frame_predicates, self.dict)
        return state

    def print_predicates(self):
        print("predicate ----")
        for f, p in sorted(zip(self.frame_numbers, self.predicates), key=lambda x: x[0]):
            print(f"predicate {f} {str(p)}")
