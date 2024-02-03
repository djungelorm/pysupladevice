from unittest.mock import Mock

from pysupladevice import channels, proto


def test_device_set_value() -> None:
    device = Mock(["set_value"])

    channel = channels.Temperature()
    channel.set_device(device, 0)

    device.set_value.assert_not_called()
    channel.update()
    device.set_value.assert_called_with(0, b"\x00\x00\x00\x00\x00\x30\x71\xc0")


def test_relay() -> None:
    channel = channels.Relay()
    assert not channel.value
    channel.set_value(False)
    assert not channel.value

    assert channel.type == proto.SUPLA_CHANNELTYPE_RELAY
    # pylint: disable=duplicate-code
    assert channel.action_trigger_caps == (
        proto.SUPLA_ACTION_CAP_TURN_ON
        | proto.SUPLA_ACTION_CAP_TURN_OFF
        | proto.SUPLA_ACTION_CAP_TOGGLE_x1
        | proto.SUPLA_ACTION_CAP_TOGGLE_x2
        | proto.SUPLA_ACTION_CAP_TOGGLE_x3
        | proto.SUPLA_ACTION_CAP_TOGGLE_x4
        | proto.SUPLA_ACTION_CAP_TOGGLE_x5
    )
    assert channel.default == 0
    assert channel.flags == proto.SUPLA_CHANNEL_FLAG_CHANNELSTATE

    assert channel.encoded_value == b"\x00\x00\x00\x00\x00\x00\x00\x00"

    channel.set_value(True)
    assert channel.value

    assert channel.encoded_value == b"\x01\x00\x00\x00\x00\x00\x00\x00"

    assert channel.set_encoded_value(b"\x00\x00\x00\x00\x00\x00\x00\x00")
    assert not channel.value
    assert channel.encoded_value == b"\x00\x00\x00\x00\x00\x00\x00\x00"

    assert channel.set_encoded_value(b"\x01\x00\x00\x00\x00\x00\x00\x00")
    assert channel.value
    assert channel.encoded_value == b"\x01\x00\x00\x00\x00\x00\x00\x00"


def test_relay_on_change() -> None:
    changes = []

    def on_change(self: channels.Relay, value: bool) -> None:
        changes.append(value)
        self.do_set_value(value)

    channel = channels.Relay(on_change=on_change)
    channel.set_value(True)
    assert channel.value
    channel.set_value(True)
    assert channel.value
    channel.set_value(False)
    assert not channel.value
    channel.set_value(True)
    assert channel.value
    channel.set_value(False)
    assert not channel.value
    channel.set_value(False)
    assert not channel.value

    assert changes == [True, True, False, True, False, False]


def test_temperature() -> None:
    channel = channels.Temperature()
    channel.set_value(21)
    assert channel.value == 21

    assert channel.type == proto.SUPLA_CHANNELTYPE_THERMOMETER
    assert channel.action_trigger_caps == 0
    assert channel.default == proto.SUPLA_CHANNELFNC_THERMOMETER
    assert channel.flags == 0

    assert channel.encoded_value == b"\x00\x00\x00\x00\x00\x00\x35\x40"

    assert channel.set_encoded_value(b"\x00\x00\x00\x00\x00\x00\x45\x40")
    assert channel.value == 42
    assert channel.encoded_value == b"\x00\x00\x00\x00\x00\x00\x45\x40"


def test_temperature_not_available() -> None:
    channel = channels.Temperature()
    assert channel.value is None
    assert channel.encoded_value == b"\x00\x00\x00\x00\x00\x30\x71\xc0"

    channel.set_value(42)
    assert channel.value is not None
    assert channel.set_encoded_value(b"\x00\x00\x00\x00\x00\x30\x71\xc0")
    assert channel.value is None


def test_humidity() -> None:
    channel = channels.Humidity()
    channel.set_value(57)
    assert channel.value == 57

    assert channel.type == proto.SUPLA_CHANNELTYPE_HUMIDITYSENSOR
    assert channel.action_trigger_caps == 0
    assert channel.default == proto.SUPLA_CHANNELFNC_HUMIDITY
    assert channel.flags == 0

    assert channel.encoded_value == b"\xc8\xcd\xfb\xff\xa8\xde\x00\x00"

    assert channel.set_encoded_value(b"\xc8\xcd\xfb\xff\x10\xa4\x00\x00")
    assert channel.value == 42
    assert channel.encoded_value == b"\xc8\xcd\xfb\xff\x10\xa4\x00\x00"


def test_humidity_not_available() -> None:
    channel = channels.Humidity()
    assert channel.value is None
    assert channel.encoded_value == b"\xc8\xcd\xfb\xff\x18\xfc\xff\xff"

    channel.set_value(42)
    assert channel.value is not None
    assert channel.set_encoded_value(b"\xc8\xcd\xfb\xff\x18\xfc\xff\xff")
    assert channel.value is None


def test_temperature_and_humidity() -> None:
    channel = channels.TemperatureAndHumidity()
    channel.set_temperature(21)
    channel.set_humidity(57)
    assert channel.temperature == 21
    assert channel.humidity == 57

    assert channel.type == proto.SUPLA_CHANNELTYPE_HUMIDITYANDTEMPSENSOR
    assert channel.action_trigger_caps == 0
    assert channel.default == proto.SUPLA_CHANNELFNC_HUMIDITYANDTEMPERATURE
    assert channel.flags == 0

    assert channel.encoded_value == b"\x08\x52\x00\x00\xa8\xde\x00\x00"

    assert channel.set_encoded_value(b"\x10\xa4\x00\x00\x90_\x01\x00")
    assert channel.temperature == 42
    assert channel.humidity == 90
    assert channel.encoded_value == b"\x10\xa4\x00\x00\x90_\x01\x00"


def test_temperature_and_humidity_not_available() -> None:
    channel = channels.TemperatureAndHumidity()
    assert channel.temperature is None
    assert channel.humidity is None
    assert channel.encoded_value == b"\xc8\xcd\xfb\xff\x18\xfc\xff\xff"

    channel.set_temperature(42)
    channel.set_humidity(42)
    assert channel.temperature is not None
    assert channel.humidity is not None
    assert channel.set_encoded_value(b"\xc8\xcd\xfb\xff\x18\xfc\xff\xff")
    assert channel.temperature is None
    assert channel.humidity is None
