import torch
import xmltodict
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor

from modules.data.base import AIModel
from modules.data.structs import ItemData, ReceiptData


class DonutModel(AIModel):
    def __init__(self, model_name: str) -> None:
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = AutoModelForVision2Seq.from_pretrained(model_name)

    def run(self, image: Image.Image) -> ReceiptData:
        text_input, image_input = self._preprocess(image)
        prediction_str = self._inference(image_input, text_input)
        receipt_dict = self._postprocess(prediction_str)
        print(receipt_dict)
        return self._formatting(receipt_dict)

    def _preprocess(self, image: Image.Image) -> tuple[torch.Tensor, torch.Tensor]:
        decoder_input_ids = self.processor.tokenizer(
            "<s_cord-v2>", add_special_tokens=False
        ).input_ids
        decoder_input_ids = torch.tensor(decoder_input_ids).unsqueeze(0)
        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        return decoder_input_ids, pixel_values

    def _inference(self, image_input: torch.Tensor, text_input: torch.Tensor) -> str:
        generation_output = self.model.generate(
            image_input,
            decoder_input_ids=text_input,
            max_length=self.model.decoder.config.max_position_embeddings,
            pad_token_id=self.processor.tokenizer.pad_token_id,
            eos_token_id=self.processor.tokenizer.eos_token_id,
            use_cache=True,
            num_beams=1,
            bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
            return_dict_in_generate=True,
        )
        return self.processor.batch_decode(generation_output.sequences)[0]

    def _postprocess(self, prediction_str: str) -> dict:
        prediction_str = prediction_str.replace(self.processor.tokenizer.eos_token, "")
        prediction_str = prediction_str.replace(self.processor.tokenizer.pad_token, "")
        prediction_str += "</s_cord-v2>"
        bill_dict = xmltodict.parse(prediction_str)
        return bill_dict

    def _formatting(self, receipt_dict: dict) -> ReceiptData:
        data_dict = receipt_dict["s_cord-v2"]
        item_names = data_dict["s_menu"]["s_nm"]
        item_counts = data_dict["s_menu"]["s_cnt"]
        item_price = data_dict["s_menu"]["s_price"]
        items = [
            ItemData(
                name=name,
                count=int(count),
                total_price=_convert_price_str_to_float(price),
            )
            for name, count, price in zip(item_names, item_counts, item_price)
        ]
        total = _convert_price_str_to_float(data_dict["s_total"]["s_total_price"])
        return ReceiptData(items={it.id: it for it in items}, total=total)


def _convert_price_str_to_float(price_str: str) -> float:
    return float(price_str.replace(",", ""))
