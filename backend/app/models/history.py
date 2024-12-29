from typing import Self, TYPE_CHECKING
from app import db
from app.helpers import DbModelMixin
from .shoppinglist import ShoppinglistItems
from .item import Item
from sqlalchemy import func
from sqlalchemy.orm import Mapped

import enum

if TYPE_CHECKING:
    from app.models import Item, Shoppinglist


class Status(enum.Enum):
    ADDED = 1
    DROPPED = -1


class History(db.Model, DbModelMixin):
    __tablename__ = "history"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)

    shoppinglist_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("shoppinglist.id"))
    item_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("item.id"))

    item: Mapped["Item"] = db.relationship("Item", uselist=False, back_populates="history")
    shoppinglist: Mapped["Shoppinglist"] = db.relationship(
        "Shoppinglist", uselist=False, back_populates="history"
    )

    status: Mapped[Status] = db.Column(db.Enum(Status))
    description: Mapped[str] = db.Column("description", db.String())

    @classmethod
    def create_added_without_save(cls, shoppinglist, item, description="") -> Self:
        return cls(
            shoppinglist_id=shoppinglist.id,
            item_id=item.id,
            status=Status.ADDED,
            description=description,
        )

    @classmethod
    def create_added(cls, shoppinglist, item, description="") -> Self:
        return cls.create_added_without_save(shoppinglist, item, description).save()

    @classmethod
    def create_dropped(
        cls, shoppinglist, item, description="", created_at=None
    ) -> Self:
        return cls(
            shoppinglist_id=shoppinglist.id,
            item_id=item.id,
            status=Status.DROPPED,
            description=description,
            created_at=created_at,
        ).save()

    def obj_to_item_dict(self) -> dict:
        res = self.item.obj_to_dict()
        res["timestamp"] = getattr(self, "created_at")
        return res

    @classmethod
    def find_added_by_shoppinglist_id(cls, shoppinglist_id: int) -> list[Self]:
        return cls.query.filter(
            cls.shoppinglist_id == shoppinglist_id, cls.status == Status.ADDED
        ).all()

    @classmethod
    def find_dropped_by_shoppinglist_id(cls, shoppinglist_id: int) -> list[Self]:
        return cls.query.filter(
            cls.shoppinglist_id == shoppinglist_id, cls.status == Status.DROPPED
        ).all()

    @classmethod
    def find_by_shoppinglist_id(cls, shoppinglist_id: int) -> list[Self]:
        return cls.query.filter(cls.shoppinglist_id == shoppinglist_id).all()

    @classmethod
    def find_all(cls) -> list[Self]:
        return cls.query.all()

    @classmethod
    def get_recent(cls, shoppinglist_id: int, limit: int = 9) -> list[Self]:
        # First get the household_id of the shopping list
        from app.models import Shoppinglist
        shoppinglist = Shoppinglist.find_by_id(shoppinglist_id)
        if not shoppinglist:
            return []
            
        if "postgresql" in db.engine.name:
            # Get items currently in any shopping list in this household
            sq = (
                db.session.query(ShoppinglistItems.item_id)
                .join(ShoppinglistItems.shoppinglist)
                .filter(Shoppinglist.household_id == shoppinglist.household_id)
                .subquery()
                .select()
            )
            # Get recent items from this household's shopping lists
            sq2 = (
                cls.query.filter(
                    cls.shoppinglist_id == shoppinglist_id,
                    cls.status == Status.DROPPED,
                    cls.item_id.notin_(sq),
                )
                .join(cls.item)  # Join with items
                .filter(Item.household_id == shoppinglist.household_id)  # Only items from this household
                .distinct(cls.item_id)
                .order_by(cls.item_id, cls.created_at.desc())
                .limit(limit)
                .subquery()
            )
            alias = db.aliased(cls, sq2)
            q = db.session.query(alias).order_by(alias.created_at.desc())
            return q.all()
        else:
            # Get items currently in any shopping list in this household
            sq = (
                db.session.query(ShoppinglistItems.item_id)
                .join(ShoppinglistItems.shoppinglist)
                .filter(Shoppinglist.household_id == shoppinglist.household_id)
                .subquery()
                .select()
            )
            # Get recent items from this household's shopping lists
            sq2 = (
                db.session.query(func.max(cls.id))
                .filter(cls.status == Status.DROPPED)
                .filter(cls.item_id.notin_(sq))
                .join(cls.item)  # Join with items
                .filter(Item.household_id == shoppinglist.household_id)  # Only items from this household
                .group_by(cls.item_id)
                .subquery()
                .select()
            )
            return (
                cls.query.filter(cls.shoppinglist_id == shoppinglist_id)
                .filter(cls.id.in_(sq2))
                .join(cls.item)  # Join with items to ensure household check
                .filter(Item.household_id == shoppinglist.household_id)  # Only items from this household
                .order_by(cls.created_at.desc(), cls.item_id)
                .limit(limit)
            )
