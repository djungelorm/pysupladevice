from pysupladevice import channels, proto
from unittest.mock import Mock


def test_device_set_value():
    device = Mock(["_set_value"])

    channel = channels.Temperature()
    channel.set_device(device, 0)

    device._set_value.assert_not_called()
    channel._update()
    device._set_value.assert_called_with(0, b"\x00\x00\x00\x00\x00\x30\x71\xc0")


def test_relay():
    channel = channels.Relay()
    assert channel.value == False
    channel.set_value(False)
    assert channel.value == False

    assert channel.type == proto.SUPLA_CHANNELTYPE_RELAY
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

    assert channel._encode_value() == b"\x00\x00\x00\x00\x00\x00\x00\x00"

    channel.set_value(True)
    assert channel.value == True

    assert channel._encode_value() == b"\x01\x00\x00\x00\x00\x00\x00\x00"


def test_relay_on_change():
    changes = []

    def on_change(value):
        changes.append(value)

    channel = channels.Relay(on_change=on_change)
    channel.set_value(True)
    channel.set_value(True)
    channel.set_value(False)
    channel.set_value(True)
    channel.set_value(False)
    channel.set_value(False)

    assert changes == [True, False, True, False]


def test_temperature():
    channel = channels.Temperature()
    channel.set_value(21)
    assert channel.value == 21

    assert channel.type == proto.SUPLA_CHANNELTYPE_THERMOMETER
    assert channel.action_trigger_caps == 0
    assert channel.default == proto.SUPLA_CHANNELFNC_THERMOMETER
    assert channel.flags == 0

    assert channel._encode_value() == b"\x00\x00\x00\x00\x00\x00\x35\x40"


def test_temperature_not_available():
    channel = channels.Temperature()
    assert channel.value is None
    assert channel._encode_value() == b"\x00\x00\x00\x00\x00\x30\x71\xc0"


def test_humidity():
    channel = channels.Humidity()
    channel.set_value(57)
    assert channel.value == 57

    assert channel.type == proto.SUPLA_CHANNELTYPE_HUMIDITYSENSOR
    assert channel.action_trigger_caps == 0
    assert channel.default == proto.SUPLA_CHANNELFNC_HUMIDITY
    assert channel.flags == 0

    assert channel._encode_value() == b"\xc8\xcd\xfb\xff\xa8\xde\x00\x00"


def test_humidity_not_available():
    channel = channels.Humidity()
    assert channel.value is None
    assert channel._encode_value() == b"\xc8\xcd\xfb\xff\x18\xfc\xff\xff"


def test_temperature_and_humidity():
    channel = channels.TemperatureAndHumidity()
    channel.set_temperature(21)
    channel.set_humidity(57)
    assert channel.temperature == 21
    assert channel.humidity == 57

    assert channel.type == proto.SUPLA_CHANNELTYPE_HUMIDITYANDTEMPSENSOR
    assert channel.action_trigger_caps == 0
    assert channel.default == proto.SUPLA_CHANNELFNC_HUMIDITYANDTEMPERATURE
    assert channel.flags == 0

    assert channel._encode_value() == b"\x08\x52\x00\x00\xa8\xde\x00\x00"


def test_temperature_and_humidity_not_available():
    channel = channels.TemperatureAndHumidity()
    assert channel.temperature is None
    assert channel.humidity is None
    assert channel._encode_value() == b"\xc8\xcd\xfb\xff\x18\xfc\xff\xff"
