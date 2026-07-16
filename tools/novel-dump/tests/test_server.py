import pytest
from server import chapter_filename, safe_path_component


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("正常书名", "正常书名"),
        ("  多余   空格  ", "多余 空格"),
        ("书名/../../危险", "书名_.._.._危险"),
        ("第1章:开始?", "第1章_开始"),
    ],
)
def test_safe_path_component(source: str, expected: str) -> None:
    assert safe_path_component(source) == expected


@pytest.mark.parametrize("source", ["", "...", "%2F"])
def test_safe_path_component_rejects_empty_values(source: str) -> None:
    with pytest.raises(ValueError):
        safe_path_component(source)


def test_chapter_filename_includes_chapter_id() -> None:
    assert chapter_filename("第一章：开始", "10001") == "10001 - 第一章_开始.txt"
