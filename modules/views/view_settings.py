import streamlit as st
from babel.core import get_global
from babel.numbers import get_currency_name

from modules.data import session_data
from modules.utils import CURRENCY_LIST


def currency_settings_view() -> str:
    currencies = list(CURRENCY_LIST.keys())
    current_currency = session_data.currency.get()
    current_idx = (
        currencies.index(current_currency) if current_currency in currencies else 0
    )
    selected_currency = st.selectbox(
        "Currency",
        list(CURRENCY_LIST.keys()),
        format_func=lambda x: f"{x}: {get_currency_name(x)}",
        index=current_idx,
    )
    return selected_currency


@st.dialog("Settings")
def settings_view() -> None:
    selected_currency = currency_settings_view()
    if st.button("Apply", key="settings_apply_button"):
        session_data.currency.set(selected_currency)
        st.rerun()
