from modules.data import session_data
from modules.data.base import AIModel

from .donut import DonutModel


def load_model(model_name: str) -> AIModel:
    model = session_data.model.get()
    if model is None:
        model = DonutModel(model_name)
        session_data.model.set(model)
    return model
