from abc import ABC, abstractmethod

from data.receipt_data import ReceiptData
from PIL import Image


class AIModel(ABC):
    "Base class of AI models"

    @abstractmethod
    def run(self, image: Image.Image) -> ReceiptData:
        """Retrieve data from the receipt.

        Args:
            image (Image.Image): the receipt photo image

        Returns:
            ReceiptData: parsed receipt data
        """
        pass
