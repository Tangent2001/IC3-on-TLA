from folseparators import separators
from structure import *


class FOLSeparator:
    def __init__(self, states, spec_info: SpecInfo, rel_dict: TLARelDict):
        self.states = states
        self.spec_info = spec_info
        self.pos_len = 0
        self.neg_len = 0
        self.imp_len = 0
        self.dict = rel_dict
        self.sig = separators.logic.Signature()
        self.ids = {}
        for s in spec_info.sort_value.keys():
            self.sig.sorts.add(s)
        for r in rel_dict.get_rel_names():
            rel = rel_dict.get_tla_rel_by_name(r)
            self.sig.relations[r] = list(map(rel_dict.get_var_sort, rel_dict.get_rel_args(rel)))
        self.sig.finalize_sorts()
        self.separator = separators.separate.HybridSeparator(self.sig, logic="universal", quiet=True)

    def _state_id(self, i: int) -> int:
        base = 10000000
        assert 0 <= i % base < len(self.states)
        offset = 0
        if i // base == 1:
            offset = self.pos_len
        elif i // base == 2:
            offset = self.neg_len + self.pos_len
        if i not in self.ids:
            # add a new state
            m = self.states[i % base + offset].get_ivy_state(self.sig)
            self.ids[i] = self.separator.add_model(m)
        return self.ids[i]

    def separate(self, pos, neg, imp):
        timer = separators.timer.UnlimitedTimer()
        base = 10000000
        self.pos_len = len(pos)
        self.neg_len = len(neg)
        self.imp_len = len(imp) * 2
        self.states = list(pos) + list(neg)
        for (i, j) in imp:
            self.states.append(i)
            self.states.append(j)
        with timer:
            f = self.separator.separate(
                pos=[self._state_id(i) for i in range(self.pos_len)],
                neg=[self._state_id(i) for i in range(base, base + self.neg_len)],
                imp=[(self._state_id(i), self._state_id(i + 1)) for i in range(base * 2, base * 2 + self.imp_len, 2)],
                max_depth=100,
                max_clauses=100,
                timer=timer
            )
        if f is None:
            raise RuntimeError("separator cannot find any invariants.")
        p = self.formula_to_predicate(f)
        return p

    def formula_to_predicate(self, formula: separators.logic.Formula):
        def term_to_expr(t: separators.logic.Term):
            if isinstance(t, separators.logic.Var):
                # TODO
                return TLAVar(t.var)
            else:
                assert False

        def formula_to_expr(f: separators.logic.Formula):
            if isinstance(f, separators.logic.And):
                return TLAAnd([formula_to_expr(a) for a in f.c])
            elif isinstance(f, separators.logic.Or):
                return TLAOr([formula_to_expr(a) for a in f.c])
            elif isinstance(f, separators.logic.Not):
                return TLANot(formula_to_expr(f.f))
            elif isinstance(f, separators.logic.Equal):
                return TLAEqual(term_to_expr(f.args[0]), term_to_expr(f.args[1]))
            elif isinstance(f, separators.logic.Relation):
                return TLARelation(f.rel, [term_to_expr(a) for a in f.args], self.dict, self.spec_info)
            elif isinstance(f, separators.logic.Exists):
                body = formula_to_expr(f.f)
                return TLAExists(TLAVar(f.var), f.sort, body)
            elif isinstance(f, separators.logic.Forall):
                body = formula_to_expr(f.f)
                return TLAForall(TLAVar(f.var), f.sort, body)
            else:
                assert False

        return formula_to_expr(formula)
