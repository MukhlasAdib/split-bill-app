from typing import Callable

import streamlit as st
from PIL import Image

from modules.data import session_data
from modules.data.receipt_data import ReceiptData
from modules.utils import format_number_to_currency

IMAGE_DISPLAY_HEIGHT = 480


def get_items_table_columns_config() -> dict:
    return {
        "name": "Name",
        "count": "Item count",
        "total_price": st.column_config.NumberColumn(
            "Total price", format="accounting"
        ),
        "id": None,
    }


def resize_to_height(image: Image.Image, target_height: int) -> Image.Image:
    width, height = image.size
    aspect_ratio = width / height
    new_width = int(target_height * aspect_ratio)
    resized_image = image.resize((new_width, target_height), Image.Resampling.LANCZOS)
    return resized_image


def image_input_view() -> Image.Image | None:
    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=["jpg", "jpeg", "png"],
        on_change=lambda: session_data.reset_receipt_data(),
    )
    if uploaded_file is None:
        return session_data.image.get()
    image = Image.open(uploaded_file)
    session_data.image.set(image)
    return image


def image_preview_view(image: Image.Image) -> None:
    st.image(resize_to_height(image, IMAGE_DISPLAY_HEIGHT), width="stretch")


@st.dialog("Confirm Data")
def receipt_read_confirmation_view(receipt: ReceiptData) -> None:
    st.markdown("### Are these data correct?")
    st.markdown("You can edit the data")
    edited_data = st.data_editor(
        receipt.to_items_df(),
        num_rows="dynamic",
        hide_index=True,
        column_config=get_items_table_columns_config(),
    )
    subtotal_str = format_number_to_currency(edited_data["total_price"].sum())
    st.markdown(f"Subtotal: {subtotal_str}")

    st.markdown("### Is this the correct total bill?")
    st.markdown("(incl. tax, services, discount, etc.)")
    edited_total = st.number_input(
        "Total price", value=receipt.total, label_visibility="collapsed"
    )
    total_str = format_number_to_currency(edited_total)
    st.markdown(f"Total: {total_str}")

    confirmation_pressed = st.button("Confirm", key="confirm_button")
    if confirmation_pressed:
        session_data.view1_auto_next_page.set(True)
        session_data.receipt_data.set(
            ReceiptData.from_items_df(edited_data, edited_total)
        )
        st.rerun()


def final_receipt_view() -> None:
    receipt = session_data.receipt_data.get()
    if receipt is None:
        st.warning("No data has been read yet...")
        return
    st.dataframe(
        receipt.to_items_df(),
        hide_index=True,
        column_config=get_items_table_columns_config(),
    )
    st.markdown(f"##### Subtotal: {format_number_to_currency(receipt.subtotal)}")
    st.markdown(f"##### Total: {format_number_to_currency(receipt.total)}")


@st.dialog("Reading your receipt...")
def read_receipt_view(
    receipt_reader: Callable[[Image.Image], ReceiptData], image: Image.Image
) -> None:
    _, col2, _ = st.columns([4.75, 0.5, 4.75])
    with col2:
        with st.spinner(""):
            receipt = receipt_reader(image)
            session_data.view1_model_result.set(receipt)
            st.rerun()


def controller(receipt_reader: Callable[[Image.Image], ReceiptData]) -> bool:
    image = image_input_view()
    if image is None:
        return False
    if session_data.receipt_data.get() is None:
        reading_data = session_data.view1_model_result.get_once()
        if reading_data is None:
            read_receipt_view(receipt_reader, image)
        else:
            receipt_read_confirmation_view(reading_data)

    st.markdown("### Your receipt data")
    col1, col2 = st.columns([3, 7])
    with col1:
        image_preview_view(image)
    with col2:
        final_receipt_view()
    return session_data.view1_auto_next_page.get_once()
