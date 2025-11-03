from abc import ABC

from PIL import Image

from modules.data.structs import ReceiptData


class AIModel(ABC):
    def run(self, image: Image.Image) -> ReceiptData: ...
