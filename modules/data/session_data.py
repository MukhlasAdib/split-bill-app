from typing import Generic

import streamlit as st
from babel import Locale, localedata
from babel.core import get_global
from PIL import Image
from typing_extensions import TypeVar

from modules.data.base import AIModel
from modules.data.structs import GroupData, ReceiptData, ReportData, SplitManager

T = TypeVar("T")
V = TypeVar("V", default=None)


class SessionDataManager(Generic[T, V]):
    _model_state = "model"

    def __init__(self, state_name: str, default: V = None) -> None:
        self.state_name = state_name
        self.default = default

    def get(self) -> T | V:
        if self.state_name not in st.session_state:
            st.session_state[self.state_name] = self.default
        return st.session_state[self.state_name]

    def set(self, value: T) -> None:
        st.session_state[self.state_name] = value

    def reset(self) -> None:
        st.session_state[self.state_name] = None

    def get_once(self) -> T | V:
        ret = self.get()
        self.reset()
        return ret


model = SessionDataManager[AIModel]("model")
currency = SessionDataManager[str, str]("currency", "IDR")
image = SessionDataManager[Image.Image]("image")
receipt_data = SessionDataManager[ReceiptData]("receipt_data")
group_data = SessionDataManager[GroupData, GroupData]("group_data", GroupData())
current_page = SessionDataManager[int, int]("current_page", 1)
split_manager = SessionDataManager[SplitManager]("split_manager")
report = SessionDataManager[ReportData]("report")
view1_model_result = SessionDataManager[ReceiptData]("view1_model_result")
view1_auto_next_page = SessionDataManager[bool, bool]("view1_auto_next_page", False)


def reset_receipt_data() -> None:
    receipt_data.reset()
    split_manager.reset()
    view1_model_result.reset()
