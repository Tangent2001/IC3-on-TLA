from typing import List, Tuple

from spec_info import SpecInfo
from tla_rel_dict import TLARelDict


class TLAFormula:
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TLAFormula): return NotImplemented
        return self._unpack() == other._unpack()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, TLAFormula): return NotImplemented
        return self._unpack() < other._unpack()

    def _unpack(self) -> Tuple:
        return ()


class TLAVar(TLAFormula):
    def __init__(self, v: str):
        self.var = v

    def __str__(self) -> str:
        return self.var

    def _unpack(self) -> Tuple: return 'Var', self.var


class TLAAnd(TLAFormula):
    def __init__(self, conjuncts: List[TLAFormula]):
        self.conjuncts = conjuncts

    def __str__(self):
        if len(self.conjuncts) == 0:
            return "TRUE"
        elif len(self.conjuncts) == 1:
            return str(self.conjuncts[0])
        return "(/\\ " + str.join("\n/\\ ", map(str, self.conjuncts)) + ")"

    def _unpack(self) -> Tuple: return "And", self.conjuncts


class TLAOr(TLAFormula):
    def __init__(self, disjuncts: List[TLAFormula]):
        self.disjuncts = disjuncts

    def __str__(self):
        if len(self.disjuncts) == 0:
            return "FALSE"
        elif len(self.disjuncts) == 1:
            return str(self.disjuncts[0])
        return "("+str.join("\\/ ", map(str, self.disjuncts)) + ")"

    def _unpack(self) -> Tuple: return "Or", self.disjuncts


class TLANot(TLAFormula):
    def __init__(self, formula):
        self.formula = formula

    def __str__(self):
        return "~(" + str(self.formula) + ")"

    def _unpack(self) -> Tuple: return "Not", self.formula


class TLAExists(TLAFormula):
    def __init__(self, var: TLAVar, sort: str, formula: TLAFormula):
        self.var = var
        self.sort = sort
        self.formula = formula

    def __str__(self):
        return "(\\E " + str(self.var) + " \\in " + self.sort + ": " + str(self.formula) + ")"

    def _unpack(self) -> Tuple: return "Exists", self.var, self.sort, self.formula


class TLAEqual(TLAFormula):
    def __init__(self, f1: TLAVar, f2: TLAVar):
        self.f1 = f1
        self.f2 = f2

    def __str__(self):
        return str(self.f1) + " = " + str(self.f2)

    def _unpack(self) -> Tuple: return "Equal", self.f1, self.f2


class TLAForall(TLAFormula):
    def __init__(self, var: TLAVar, sort: str, formula: TLAFormula):
        self.var = var
        self.sort = sort
        self.formula = formula

    def __str__(self):
        return "(\\A " + str(self.var) + " \\in " + self.sort + ": " + str(self.formula) + ")"

    def _unpack(self) -> Tuple: return "Forall", self.var, self.sort, self.formula


class TLAUnresolved(TLAFormula):
    def __init__(self, inv_str):
        self.inv_str = inv_str

    def __str__(self):
        return "(" + self.inv_str + ")"

    def _unpack(self) -> Tuple: return "Unresolved", self.inv_str


class TLARelation(TLAFormula):
    def __init__(self, relation: str, args: List[TLAVar], rel_dic: TLARelDict, spec_info: SpecInfo):
        self.relation = relation
        self.args = args
        self.rel_dic = rel_dic
        self.spec_info = spec_info

    def __str__(self):
        # args_str_list = map(str, self.args)
        return self.substitute_args("(" + self.rel_dic.get_tla_rel_by_name(self.relation) + ")")

    def substitute_args(self, rel: str):
        pos = []
        for c in self.spec_info.const_sort.keys():
            if rel.find(c) != -1:
                pos.append((c, rel.find(c)))
        pos.sort(key=lambda x: x[1])
        i = 0
        for c, p in pos:
            rel = rel.replace(c, str(self.args[i]))
            i += 1
        return rel

    def _unpack(self) -> Tuple:
        return "Relation", self.relation
