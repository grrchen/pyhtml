import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pyhtml import Tokenizer, Parser, Compiler, compile_pyhtml, SyntaxError


def test_compiler1():
    src: str = """div1:"""
    html = compile_pyhtml(src)
    assert html == """<div1>
</div1>"""


def test_compiler2():
    src: str = """div1:
"""
    html = compile_pyhtml(src)
    assert html == """<div1>
</div1>"""


def test_compiler3():
    src: str = """div1:
    div2:
"""
    html = compile_pyhtml(src)
    assert html == """<div1>
    <div2>
    </div2>
</div1>"""


def test_compiler_attribute():
    src: str = """div1:
    class = "window"
"""
    html = compile_pyhtml(src)
    assert html == """<div1 class='window'>
</div1>"""


def test_compiler_attribute1():
    src: str = """div1 class = "window":
"""
    html = compile_pyhtml(src)
    assert html == """<div1 class='window'>
</div1>"""


def test_compiler_attributes():
    src: str = """div1:
    class = "window"
    style = "position: absolute; left: 10px; top 10px;"
"""
    html = compile_pyhtml(src)
    assert html == """<div1 class='window' style='position: absolute; left: 10px; top 10px;'>
</div1>"""


def test_compiler_attributes2():
    src: str = """div1 class = "window" style = "position: absolute; left: 10px; top 10px;":
"""
    html = compile_pyhtml(src)
    assert html == """<div1 class='window' style='position: absolute; left: 10px; top 10px;'>
</div1>"""


def test_compiler_attributes3():
    src: str = """div1 class = "window" style = "position: absolute; left: 10px; top 10px;":
    div2 class = "window":
"""
    html = compile_pyhtml(src)
    assert html == """<div1 class='window' style='position: absolute; left: 10px; top 10px;'>
    <div2 class='window'>
    </div2>
</div1>"""


def test_compiler_attributes4():
    src: str = """div1 class = "window" style = "position: absolute; left: 10px; top 10px;":
    div2 class = "window":
        << "test123"
"""
    html = compile_pyhtml(src)
    assert html == """<div1 class='window' style='position: absolute; left: 10px; top 10px;'>
    <div2 class='window'>
test123
    </div2>
</div1>"""


def test_compiler_text1():
    src: str = """div1:
    << "test123456"
"""

    html = compile_pyhtml(src)
    assert html == """<div1>
test123456
</div1>"""


def test_compiler_text2():
    src: str = """div1:
    << "test123"
    << "test123456"
"""
    html = compile_pyhtml(src)
    assert html == """<div1>
test123
test123456
</div1>"""


def test_compiler_text3():
    src: str = """div1:
    << "test123"
    div2:
        << "test123456"
"""
    html = compile_pyhtml(src)
    assert html == """<div1>
test123
    <div2>
test123456
    </div2>
</div1>"""


def test_compiler_text3():
    src: str = """div1:
    << "test123"
    div2:
        << "test123456"
    div3:
        << "test123456789"
"""
    html = compile_pyhtml(src)
    assert html == """<div1>
test123
    <div2>
test123456
    </div2>
    <div3>
test123456789
    </div3>
</div1>"""


def test_compiler_multiline_text():
    src: str = """div1:
    << "test123"
    << "test123456"
"""

    html = compile_pyhtml(src)
    assert html == """<div1>
test123
test123456
</div1>"""

def test_compiler_multiline_text2():
    src: str = """div1:
    << "test123
test123456"
"""

    html = compile_pyhtml(src)
    assert html == """<div1>
test123
test123456
</div1>"""


def test_compiler2():
    src: str = """div1:
        style="position: absolute;"
        div2:
            << "test"
            class = "window"
            style = "background-color: blue"
            div3:
                << "test123"
            div4:
                << "test123456"
"""

    html = compile_pyhtml(src)
    assert html == """<div1 style='position: absolute;'>
        <div2 class='window' style='background-color: blue'>
test
            <div3>
test123
            </div3>
            <div4>
test123456
            </div4>
        </div2>
</div1>"""


def test_invalid_syntax():
    src: str = """div1:
        style="position: absolute;"
        div2:
            class =
            div3:
                << "test123"

"""
    try:
        html = compile_pyhtml(src)
    except SyntaxError as err:
        assert err.line == 5
        assert err.row == 13

