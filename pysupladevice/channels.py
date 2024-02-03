from __future__ import annotations

import ctypes
from collections.abc import Callable
from typing import Any

from pysupladevice import proto
from pysupladevice.device import Device


class Channel:  # pylint: disable=too-few-public-methods
    def __init__(self) -> None:
        self._device: Device | None = None
        self._channel_number: int | None = None

    def set_device(self, device: Device, channel_number: int) -> None:
        self._device = device
        self._channel_number = channel_number

    def update(self) -> None:
        if self._device is not None:
            assert self._channel_number is not None
            self._device.set_value(self._channel_number, self.encoded_value)

    @property
    def type(self) -> int:
        raise NotImplementedError  # pragma: no cover

    @property
    def action_trigger_caps(self) -> int:
        raise NotImplementedError  # pragma: no cover

    @property
    def default(self) -> Any:
        raise NotImplementedError  # pragma: no cover

    @property
    def flags(self) -> int:
        raise NotImplementedError  # pragma: no cover

    @property
    def encoded_value(self) -> bytes:
        raise NotImplementedError  # pragma: no cover


class Relay(Channel):
    def __init__(
        self,
        default: bool = False,
        on_change: Callable[[Relay, bool], None] | None = None,
    ):
        super().__init__()
        self._default = default
        self._value = default
        self._on_change = on_change

    @property
    def value(self) -> bool:
        return self._value

    @property
    def type(self) -> int:
        return proto.SUPLA_CHANNELTYPE_RELAY

    @property
    def action_trigger_caps(self) -> int:
        return (
            proto.SUPLA_ACTION_CAP_TURN_ON
            | proto.SUPLA_ACTION_CAP_TURN_OFF
            | proto.SUPLA_ACTION_CAP_TOGGLE_x1
            | proto.SUPLA_ACTION_CAP_TOGGLE_x2
            | proto.SUPLA_ACTION_CAP_TOGGLE_x3
            | proto.SUPLA_ACTION_CAP_TOGGLE_x4
            | proto.SUPLA_ACTION_CAP_TOGGLE_x5
        )

    @property
    def default(self) -> bool:
        return self._default

    @property
    def flags(self) -> int:
        return proto.SUPLA_CHANNEL_FLAG_CHANNELSTATE

    def do_set_value(self, value: bool) -> None:
        self._value = value
        self.update()

    def set_value(self, value: bool) -> bool:
        if self._on_change is None:
            self.do_set_value(value)
        else:
            self._on_change(self, value)
        return True

    @property
    def encoded_value(self) -> bytes:
        return bytes(ctypes.c_uint64(self._value))

    def set_encoded_value(self, value: bytes) -> bool:
        decoded_value = bool(ctypes.c_uint64.from_buffer_copy(value).value)
        return self.set_value(decoded_value)


class Temperature(Channel):
    def __init__(self) -> None:
        super().__init__()
        self._value: float | None = None

    @property
    def value(self) -> float | None:
        return self._value

    @property
    def type(self) -> int:
        return proto.SUPLA_CHANNELTYPE_THERMOMETER

    @property
    def action_trigger_caps(self) -> int:
        return 0

    @property
    def default(self) -> int:
        return proto.SUPLA_CHANNELFNC_THERMOMETER

    @property
    def flags(self) -> int:
        return 0

    def set_value(self, value: float) -> bool:
        self._value = value
        self.update()
        return True

    @property
    def encoded_value(self) -> bytes:
        value = self._value
        if value is None:
            value = proto.SUPLA_TEMPERATURE_NOT_AVAILABLE
        return bytes(ctypes.c_double(value))

    def set_encoded_value(self, value: bytes) -> bool:
        self._value = ctypes.c_double.from_buffer_copy(value).value
        if self._value == proto.SUPLA_TEMPERATURE_NOT_AVAILABLE:
            self._value = None
        self.update()
        return True


class Humidity(Channel):
    def __init__(self) -> None:
        super().__init__()
        self._value: float | None = None

    @property
    def value(self) -> float | None:
        return self._value

    @property
    def type(self) -> int:
        return proto.SUPLA_CHANNELTYPE_HUMIDITYSENSOR

    @property
    def action_trigger_caps(self) -> int:
        return 0

    @property
    def default(self) -> int:
        return proto.SUPLA_CHANNELFNC_HUMIDITY

    @property
    def flags(self) -> int:
        return 0

    def set_value(self, value: float) -> bool:
        self._value = value
        self.update()
        return True

    @property
    def encoded_value(self) -> bytes:
        value = self._value
        if value is None:
            value = proto.SUPLA_HUMIDITY_NOT_AVAILABLE
        temp_data = bytes(
            ctypes.c_int32(int(proto.SUPLA_TEMPERATURE_NOT_AVAILABLE * 1000))
        )
        humi_data = bytes(ctypes.c_int32(int(value * 1000)))
        return temp_data + humi_data

    def set_encoded_value(self, value: bytes) -> bool:
        self._value = ctypes.c_int32.from_buffer_copy(value[4:8]).value / 1000
        if self._value == proto.SUPLA_HUMIDITY_NOT_AVAILABLE:
            self._value = None
        self.update()
        return True


class TemperatureAndHumidity(Channel):
    def __init__(self) -> None:
        super().__init__()
        self._temperature: float | None = None
        self._humidity: float | None = None

    @property
    def temperature(self) -> float | None:
        return self._temperature

    @property
    def humidity(self) -> float | None:
        return self._humidity

    @property
    def type(self) -> int:
        return proto.SUPLA_CHANNELTYPE_HUMIDITYANDTEMPSENSOR

    @property
    def action_trigger_caps(self) -> int:
        return 0

    @property
    def default(self) -> int:
        return proto.SUPLA_CHANNELFNC_HUMIDITYANDTEMPERATURE

    @property
    def flags(self) -> int:
        return 0

    def set_temperature(self, value: float) -> bool:
        self._temperature = value
        self.update()
        return True

    def set_humidity(self, value: float) -> bool:
        self._humidity = value
        self.update()
        return True

    @property
    def encoded_value(self) -> bytes:
        temp = self._temperature
        humi = self._humidity
        if temp is None:
            temp = proto.SUPLA_TEMPERATURE_NOT_AVAILABLE
        if humi is None:
            humi = proto.SUPLA_HUMIDITY_NOT_AVAILABLE
        temp_data = bytes(ctypes.c_int32(int(temp * 1000)))
        humi_data = bytes(ctypes.c_int32(int(humi * 1000)))
        return temp_data + humi_data

    def set_encoded_value(self, value: bytes) -> bool:
        self._temperature = ctypes.c_int32.from_buffer_copy(value[0:4]).value / 1000
        self._humidity = ctypes.c_int32.from_buffer_copy(value[4:8]).value / 1000
        if self._temperature == proto.SUPLA_TEMPERATURE_NOT_AVAILABLE:
            self._temperature = None
        if self._humidity == proto.SUPLA_HUMIDITY_NOT_AVAILABLE:
            self._humidity = None
        self.update()
        return True
