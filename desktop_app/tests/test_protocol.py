import pytest

from app.serial.protocol import ProtocolError, parse_frame


def test_parse_valid_frame():
    state = parse_frame("T,0,1,0,1,512,498,1023,14\n")

    assert state.buttons == {
        "btn1": False,
        "btn2": True,
        "btn3": False,
        "btn4": True,
    }
    assert state.axes_raw == {
        "stick1_x": 512,
        "stick1_y": 498,
        "stick2_x": 1023,
        "stick2_y": 14,
    }


@pytest.mark.parametrize(
    "frame",
    [
        "",
        "X,0,0,0,0,512,512,512,512",
        "T,0,0,0,0,512",
        "T,a,0,0,0,512,512,512,512",
    ],
)
def test_parse_invalid_frame(frame):
    with pytest.raises(ProtocolError):
        parse_frame(frame)
