from app.core.models import AppConfig, AxisMapping, ButtonMapping
from app.profiles.schema import config_from_dict, config_to_dict


def test_config_roundtrip():
    config = AppConfig(
        serial_port="COM7",
        baudrate=115200,
        mapping_enabled=True,
    )
    config.buttons["btn1"] = ButtonMapping(
        mode="keyboard",
        behavior="hold",
        key="space",
    )
    config.axes["stick1_x"] = AxisMapping(
        mode="digital_axis",
        negative_key="a",
        positive_key="d",
    )
    config.axes["stick1_x"].calibration.deadzone = 0.1

    restored = config_from_dict(config_to_dict(config))

    assert restored.serial_port == "COM7"
    assert restored.baudrate == 115200
    assert restored.mapping_enabled is True
    assert restored.buttons["btn1"].mode == "keyboard"
    assert restored.buttons["btn1"].behavior == "hold"
    assert restored.axes["stick1_x"].mode == "digital_axis"
    assert restored.axes["stick1_x"].calibration.deadzone == 0.1
