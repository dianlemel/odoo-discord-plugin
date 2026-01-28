from .points import PointsCog
from .bind import BindCog
from .buy import BuyCog
from .gift import GiftCog
from .autodelete import AutodeleteCog

# 所有要載入的 Cogs
COGS = [
    PointsCog,
    BindCog,
    BuyCog,
    GiftCog,
    AutodeleteCog,
]
