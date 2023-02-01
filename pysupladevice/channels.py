import ctypes
from . import proto


class Channel(object):
    def __init__(self):
        self._device = None
        self._channel_number = None

    def set_device(self, device, channel_number):
        self._device = device
        self._channel_number = channel_number

    def _update(self):
        if self._device is not None:
            self._device._set_value(self._channel_number, self._encoded_value)


class Relay(Channel):
    def __init__(self, default=False, on_change=None):
        super().__init__()
        self._default = default
        self._value = default
        self._on_change = on_change

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return proto.SUPLA_CHANNELTYPE_RELAY

    @property
    def action_trigger_caps(self):
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
    def default(self):
        return self._default

    @property
    def flags(self):
        return proto.SUPLA_CHANNEL_FLAG_CHANNELSTATE

    def do_set_value(self, value):
        self._value = value
        self._update()

    def set_value(self, value):
        if self._on_change is None:
            self.do_set_value(value)
        else:
            self._on_change(self, value)
        return True

    @property
    def _encoded_value(self):
        return bytes(ctypes.c_uint64(self._value))

    def _set_encoded_value(self, value):
        if ctypes.c_uint64.from_buffer_copy(value).value == 1:
            decoded_value = True
        else:
            decoded_value = False
        return self.set_value(decoded_value)


class Temperature(Channel):
    def __init__(self):
        super().__init__()
        self._value = None

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return proto.SUPLA_CHANNELTYPE_THERMOMETER

    @property
    def action_trigger_caps(self):
        return 0

    @property
    def default(self):
        return proto.SUPLA_CHANNELFNC_THERMOMETER

    @property
    def flags(self):
        return 0

    def set_value(self, value):
        self._value = value
        self._update()
        return True

    @property
    def _encoded_value(self):
        value = self._value
        if value is None:
            value = proto.SUPLA_TEMPERATURE_NOT_AVAILABLE
        return bytes(ctypes.c_double(value))

    def _set_encoded_value(self, value):
        self._value = ctypes.c_double.from_buffer_copy(value).value
        if self._value == proto.SUPLA_TEMPERATURE_NOT_AVAILABLE:
            self._value = None
        self._update()
        return True


class Humidity(Channel):
    def __init__(self):
        super().__init__()
        self._value = None

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return proto.SUPLA_CHANNELTYPE_HUMIDITYSENSOR

    @property
    def action_trigger_caps(self):
        return 0

    @property
    def default(self):
        return proto.SUPLA_CHANNELFNC_HUMIDITY

    @property
    def flags(self):
        return 0

    def set_value(self, value):
        self._value = value
        self._update()
        return True

    @property
    def _encoded_value(self):
        value = self._value
        if value is None:
            value = proto.SUPLA_HUMIDITY_NOT_AVAILABLE
        temp_data = bytes(
            ctypes.c_int32(int(proto.SUPLA_TEMPERATURE_NOT_AVAILABLE * 1000))
        )
        humi_data = bytes(ctypes.c_int32(int(value * 1000)))
        return temp_data + humi_data

    def _set_encoded_value(self, value):
        self._value = ctypes.c_int32.from_buffer_copy(value[4:8]).value / 1000
        if self._value == proto.SUPLA_HUMIDITY_NOT_AVAILABLE:
            self._value = None
        self._update()
        return True


class TemperatureAndHumidity(Channel):
    def __init__(self):
        super().__init__()
        self._temperature = None
        self._humidity = None

    @property
    def temperature(self):
        return self._temperature

    @property
    def humidity(self):
        return self._humidity

    @property
    def type(self):
        return proto.SUPLA_CHANNELTYPE_HUMIDITYANDTEMPSENSOR

    @property
    def action_trigger_caps(self):
        return 0

    @property
    def default(self):
        return proto.SUPLA_CHANNELFNC_HUMIDITYANDTEMPERATURE

    @property
    def flags(self):
        return 0

    def set_temperature(self, value):
        self._temperature = value
        return self._update()

    def set_humidity(self, value):
        self._humidity = value
        return self._update()

    @property
    def _encoded_value(self):
        temp = self._temperature
        humi = self._humidity
        if temp is None:
            temp = proto.SUPLA_TEMPERATURE_NOT_AVAILABLE
        if humi is None:
            humi = proto.SUPLA_HUMIDITY_NOT_AVAILABLE
        temp_data = bytes(ctypes.c_int32(int(temp * 1000)))
        humi_data = bytes(ctypes.c_int32(int(humi * 1000)))
        return temp_data + humi_data

    def _set_encoded_value(self, value):
        self._temperature = ctypes.c_int32.from_buffer_copy(value[0:4]).value / 1000
        self._humidity = ctypes.c_int32.from_buffer_copy(value[4:8]).value / 1000
        if self._temperature == proto.SUPLA_TEMPERATURE_NOT_AVAILABLE:
            self._temperature = None
        if self._humidity == proto.SUPLA_HUMIDITY_NOT_AVAILABLE:
            self._humidity = None
        self._update()
        return True
