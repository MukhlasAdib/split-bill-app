from dataclasses import asdict, dataclass, field
from typing import ClassVar, Self

import pandas as pd

from modules.utils import format_number_to_currency


class IDGenerator:
    num: ClassVar[int] = 0

    @classmethod
    def get(cls) -> int:
        cls.num += 1
        return cls.num


class ItemIDGenerator(IDGenerator):
    pass


class AssignedItemIDGenerator(IDGenerator):
    pass


class ParticipantIDGenerator(IDGenerator):
    pass


@dataclass
class ItemData:
    name: str
    count: int
    total_price: float

    id: int = field(default_factory=ItemIDGenerator.get)

    @property
    def unit_price(self) -> float:
        return self.total_price / self.count


@dataclass
class AssignedItemData:
    item: ItemData
    assigned_count: int = 0

    id: int = field(default_factory=AssignedItemIDGenerator.get)

    def set_count(self, count: int) -> None:
        self.assigned_count = count


@dataclass
class ReceiptData:
    items: dict[int, ItemData]
    total: float

    @property
    def subtotal(self) -> float:
        return sum(item.total_price for item in self.items.values())

    def to_items_df(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(item) for item in self.items.values()])

    @classmethod
    def from_items_df(cls, items_df: pd.DataFrame, total: float) -> "ReceiptData":
        items = [
            ItemData(
                name=row["name"],
                count=row["count"],
                total_price=row["total_price"],
            )
            for _, row in items_df.iterrows()
        ]
        return cls(items={it.id: it for it in items}, total=total)


@dataclass
class ParticipantData:
    name: str

    id: int = field(default_factory=ParticipantIDGenerator.get)


@dataclass
class GroupData:
    participants: dict[int, ParticipantData] = field(default_factory=dict)

    def add(self, name: str) -> None:
        new_participant = ParticipantData(name=name)
        self.participants[new_participant.id] = new_participant

    def remove(self, participant_id: int) -> None:
        if participant_id in self.participants:
            self.participants.pop(participant_id)

    def __len__(self) -> int:
        return len(self.participants)


class SplitManager:
    def __init__(self, group_data: GroupData, receipt_data: ReceiptData) -> None:
        self.group_data = group_data
        self.receipt_data = receipt_data
        self.participant_assignments: dict[int, list[AssignedItemData]] = {}

    @property
    def item_ids(self) -> list[int]:
        return [it.id for it in self.get_all_items()]

    def get_all_participants(self) -> list[ParticipantData]:
        return list(self.group_data.participants.values())

    def get_all_items(self) -> list[ItemData]:
        return list(self.receipt_data.items.values())

    def get_item(self, item_id: int) -> ItemData:
        return self.receipt_data.items[item_id]

    def get_items_assignment_total(self, item_id: int) -> int:
        total = 0
        for _, assigned_items in self.participant_assignments.items():
            total += sum(
                assigned_item.assigned_count
                for assigned_item in assigned_items
                if assigned_item.item.id == item_id
            )
        return total

    def get_participant_items_list(self, participant_id: int) -> list[AssignedItemData]:
        if participant_id not in self.participant_assignments:
            self.participant_assignments[participant_id] = []
        return self.participant_assignments[participant_id]

    def add_item(self, participant_id: int, item_id: int) -> None:
        participant_items = self.get_participant_items_list(participant_id)
        participant_items.append(
            AssignedItemData(self.get_item(item_id), assigned_count=1)
        )

    def remove_items(self, participant_id: int, item_idxs: list[int]) -> None:
        participant_items = self.get_participant_items_list(participant_id)
        for idx in item_idxs:
            participant_items.pop(idx)

    def remove_participant(self, participant_id: int) -> None:
        self.group_data.remove(participant_id)
        if participant_id in self.participant_assignments:
            self.participant_assignments.pop(participant_id)


@dataclass
class PurchasedItemReportData:
    item_id: int
    name: str
    purchased_count: int
    unit_price: float

    @classmethod
    def from_item_data(cls, item_assignment: AssignedItemData) -> Self:
        return cls(
            item_id=item_assignment.item.id,
            name=item_assignment.item.name,
            purchased_count=item_assignment.assigned_count,
            unit_price=item_assignment.item.unit_price,
        )

    @property
    def total(self) -> float:
        return self.purchased_count * self.unit_price


@dataclass
class ParticipantReportData:
    participant_id: int
    name: str
    purchased_items: list[PurchasedItemReportData]
    purchased_subtotal: float
    purchased_total: float

    @property
    def purchased_others(self) -> float:
        return self.purchased_total - self.purchased_subtotal

    @classmethod
    def from_split_manager(
        cls,
        participant: ParticipantData,
        assigned_items: list[AssignedItemData],
        order_subtotal: float,
        order_total: float,
    ) -> Self:
        purchased_items = [
            PurchasedItemReportData.from_item_data(it) for it in assigned_items
        ]
        subtotal = sum(it.total for it in purchased_items)
        total = (subtotal / order_subtotal) * order_total
        return cls(
            participant_id=participant.id,
            name=participant.name,
            purchased_items=purchased_items,
            purchased_subtotal=subtotal,
            purchased_total=total,
        )

    def to_dataframe_display(self) -> pd.DataFrame:
        rows = [
            {
                "Name": it.name,
                "Count": it.purchased_count,
                "Unit price": format_number_to_currency(it.unit_price),
                "Total": format_number_to_currency(it.total),
            }
            for it in self.purchased_items
        ]
        return pd.DataFrame(
            rows, columns=["Name", "Count", "Unit price", "Total"]
        ).set_index("Name")


@dataclass
class ReportData:
    participants_reports: list[ParticipantReportData]

    @classmethod
    def from_split_manager(cls, manager: SplitManager) -> Self:
        order_subtotal = manager.receipt_data.subtotal
        order_total = manager.receipt_data.total
        return cls(
            participants_reports=[
                ParticipantReportData.from_split_manager(
                    p,
                    manager.get_participant_items_list(p.id),
                    order_subtotal,
                    order_total,
                )
                for p in manager.get_all_participants()
            ],
        )
