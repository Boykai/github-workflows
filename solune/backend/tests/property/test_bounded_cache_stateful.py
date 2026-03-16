from __future__ import annotations

from collections import OrderedDict

from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from src.utils import BoundedDict, BoundedSet


class BoundedCacheStateMachine(RuleBasedStateMachine):
    def _record_eviction(self, key: str, value: int) -> None:
        self.evicted.append((key, value))

    @initialize()
    def init_state(self) -> None:
        self.maxlen = 3
        self.evicted: list[tuple[str, int]] = []
        self.expected_evictions: list[tuple[str, int]] = []
        self.model_dict: OrderedDict[str, int] = OrderedDict()
        self.model_set: OrderedDict[str, None] = OrderedDict()
        self.bound_dict = BoundedDict[str, int](maxlen=self.maxlen, on_evict=self._record_eviction)
        self.bound_set = BoundedSet[str](maxlen=self.maxlen)

    @rule(key=st.text(min_size=1, max_size=5), value=st.integers(min_value=0, max_value=100))
    def add_to_dict(self, key: str, value: int) -> None:
        if key in self.model_dict:
            self.model_dict.move_to_end(key)
            self.model_dict[key] = value
        else:
            if len(self.model_dict) >= self.maxlen:
                self.expected_evictions.append(self.model_dict.popitem(last=False))
            self.model_dict[key] = value
        self.bound_dict[key] = value

    @rule(item=st.text(min_size=1, max_size=5))
    def add_to_set(self, item: str) -> None:
        if item in self.model_set:
            self.model_set.move_to_end(item)
        else:
            if len(self.model_set) >= self.maxlen:
                self.model_set.popitem(last=False)
            self.model_set[item] = None
        self.bound_set.add(item)

    @rule(key=st.text(min_size=1, max_size=5))
    def remove_from_dict(self, key: str) -> None:
        self.model_dict.pop(key, None)
        self.bound_dict.pop(key, None)

    @rule(item=st.text(min_size=1, max_size=5))
    def remove_from_set(self, item: str) -> None:
        self.model_set.pop(item, None)
        self.bound_set.discard(item)

    @invariant()
    def dict_len_never_exceeds_maxlen(self) -> None:
        assert len(self.bound_dict) <= self.maxlen
        assert list(self.bound_dict.items()) == list(self.model_dict.items())

    @invariant()
    def set_len_never_exceeds_maxlen(self) -> None:
        assert len(self.bound_set) <= self.maxlen
        assert list(self.bound_set) == list(self.model_set)

    @invariant()
    def eviction_callback_matches_capacity_pressure(self) -> None:
        assert self.evicted == self.expected_evictions


TestBoundedCacheStateMachine = BoundedCacheStateMachine.TestCase
