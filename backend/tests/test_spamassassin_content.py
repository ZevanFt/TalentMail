"""SpamAssassin 内容构造测试（纯函数，不依赖 Docker）"""
from types import SimpleNamespace

from core.spamassassin import _build_eml_content, _html_to_text


class TestHtmlToText:
    def test_strips_tags(self):
        assert _html_to_text("<p>Hello <b>World</b></p>") == "Hello World"

    def test_unescapes_entities(self):
        assert _html_to_text("a &amp; b") == "a & b"

    def test_empty(self):
        assert _html_to_text("") == ""


class TestBuildEmlContent:
    def test_uses_text_body(self):
        report = SimpleNamespace(
            id=1,
            email=SimpleNamespace(
                subject="Hello",
                sender="a@example.com",
                recipients="b@example.com",
                body_text="plain body",
                body_html="<p>html</p>",
            ),
        )
        content = _build_eml_content(report).decode("utf-8")
        assert "From: a@example.com" in content
        assert "To: b@example.com" in content
        assert "Subject: Hello" in content
        assert "plain body" in content

    def test_falls_back_to_html(self):
        report = SimpleNamespace(
            id=2,
            email=SimpleNamespace(
                subject=None,
                sender=None,
                recipients=None,
                body_text=None,
                body_html="<p>only html</p>",
            ),
        )
        content = _build_eml_content(report).decode("utf-8")
        assert "only html" in content
        assert "(no subject)" in content
        assert "unknown@example.invalid" in content

    def test_empty_body_placeholder(self):
        report = SimpleNamespace(
            id=3,
            email=SimpleNamespace(
                subject="s",
                sender="a@b.c",
                recipients="d@e.f",
                body_text="",
                body_html="",
            ),
        )
        content = _build_eml_content(report).decode("utf-8")
        assert "(empty body)" in content
