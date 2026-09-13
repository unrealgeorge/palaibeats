"""Generic page-chunking helper for Discord select menus (25-option cap)."""

from __future__ import annotations

from typing import Sequence, TypeVar

T = TypeVar("T")

PAGE_SIZE = 25


def paginate(items: Sequence[T], page: int, page_size: int = PAGE_SIZE) -> list[T]:
    start = page * page_size
    return list(items[start : start + page_size])


def page_count(total_items: int, page_size: int = PAGE_SIZE) -> int:
    if total_items == 0:
        return 1
    return (total_items - 1) // page_size + 1
