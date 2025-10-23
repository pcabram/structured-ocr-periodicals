"""Test that Pydantic schemas validate correctly."""

import pytest
from pydantic import ValidationError

from schemas.stage1_page import Stage1PageModel


def test_valid_page():
    """Schema accepts valid page data."""
    data = {
        "items": [
            {
                "item_class": "prose",
                "item_text_raw": "Sample text",
            }
        ]
    }
    page = Stage1PageModel(**data)
    assert len(page.items) == 1
    assert page.items[0].item_class == "prose"


def test_invalid_item_class():
    """Schema rejects invalid item_class."""
    data = {
        "items": [
            {
                "item_class": "invalid_type",
                "item_text_raw": "Text",
            }
        ]
    }
    with pytest.raises(ValidationError):
        Stage1PageModel(**data)


def test_empty_page():
    """Schema accepts empty items list."""
    data = {"items": []}
    page = Stage1PageModel(**data)
    assert len(page.items) == 0
