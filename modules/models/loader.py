from enum import Enum

from modules.data import session_data
from modules.data.base import AIModel
from modules.utils import SettingsError

from .donut import DonutModel
from .gemini import GeminiModel


class ModelNames(Enum):
    GEMINI = "Gemini"
    DONUT = "Donut"


MODELS_LOADER = {ModelNames.GEMINI: GeminiModel, ModelNames.DONUT: DonutModel}


def _load_model() -> AIModel:
    model_name = session_data.model_name.get()
    if model_name not in MODELS_LOADER:
        raise SettingsError(f"Model name is not recognized {model_name}")
    return MODELS_LOADER[model_name]()


def get_model() -> AIModel:
    model = session_data.model.get()
    if model is None:
        model = _load_model()
        session_data.model.set(model)
    return model
