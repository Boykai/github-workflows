from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from src.services.agents.agent_mcp_sync import _parse_agent_file, _serialize_agent_file

_yaml_key = st.from_regex(r"[a-z][a-z0-9_-]{0,8}", fullmatch=True)
_yaml_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    max_size=24,
)
_yaml_value = st.one_of(
    _yaml_text,
    st.lists(_yaml_text, max_size=3),
    st.dictionaries(_yaml_key, _yaml_text, max_size=3),
)
_frontmatter = st.dictionaries(_yaml_key, _yaml_value, min_size=1, max_size=4)
_body = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cs",),
        blacklist_characters="\x00\x85\u2028\u2029",
    ),
    max_size=120,
).filter(lambda value: value == "" or any(not char.isspace() for char in value))


@settings(max_examples=150)
@given(frontmatter=_frontmatter, body=_body)
def test_agent_file_parse_serialize_roundtrip(frontmatter: dict, body: str) -> None:
    serialized = _serialize_agent_file(frontmatter, body)

    parsed_frontmatter, parsed_body = _parse_agent_file(serialized)

    assert parsed_frontmatter == frontmatter
    assert parsed_body == body.lstrip()


@settings(max_examples=120)
@given(body=_body.filter(lambda value: not value.startswith("---\n")))
def test_non_frontmatter_content_roundtrips_as_plain_body(body: str) -> None:
    parsed_frontmatter, parsed_body = _parse_agent_file(body)

    assert parsed_frontmatter is None
    assert parsed_body == body
