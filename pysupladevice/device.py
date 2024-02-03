from __future__ import annotations

import ctypes
import socket
import time
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any

from pysupladevice import network, proto

if TYPE_CHECKING:
    from pysupladevice.channels import Channel


class DeviceError(Exception):
    pass


class DeviceState(Enum):
    CONNECTING = 1
    REGISTERING = 2
    CONNECTED = 3


class BufferState(Enum):
    PACKET_AVAILABLE = 1
    INCOMPLETE = 2
    INVALID = 3


class Device:  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint:disable=too-many-arguments
        self,
        server: str,
        email: str,
        guid: bytes,
        authkey: bytes,
        name: str | None = None,
        version: str | None = None,
        port: int = 2016,
        secure: bool = True,
        debug: bool = False,
    ) -> None:
        self._start_time = time.time()
        self._socket = network.Socket(server, port, secure)
        self._server = server
        self._port = port
        self._secure = secure
        self._email = email
        self._name = name or ""
        self._version = version or ""
        self._guid = guid
        self._authkey = authkey
        self._channels: list[Channel] = []
        self._debug = debug

        self._state = DeviceState.CONNECTING
        self._rr_id = 1
        self._recv_buffer = b""

        self._ping_timeout = 15
        self._last_ping: float = 0

    @property
    def state(self) -> DeviceState:
        return self._state

    def add(self, channel: Channel) -> None:
        channel_number = len(self._channels)
        self._channels.append(channel)
        channel.set_device(self, channel_number)

    def connect(self) -> None:
        while self._state != DeviceState.CONNECTED:
            self.loop()

    @property
    def socket(self) -> socket.socket:
        return self._socket.socket

    def loop_forever(self) -> None:
        while True:
            self.loop()

    def loop(self) -> None:
        try:
            self._update()
        except network.NetworkError as exn:
            if self._debug:
                print(exn)
            self._socket = network.Socket(self._server, self._port, self._secure)
            self._state = DeviceState.CONNECTING

    def _update(self) -> None:
        if self._state == DeviceState.CONNECTING:
            self._register()
            self._state = DeviceState.REGISTERING
            return

        if self._state == DeviceState.CONNECTED:
            now = time.time()
            if now - self._last_ping > self._ping_timeout:
                self._send_ping()
                self._last_ping = now
                return

        self._recv_buffer += self._socket.read()

        state, packet_size = self._check_for_packet()
        if state == BufferState.INVALID:
            raise network.NetworkError("Invalid data received")
        if state == BufferState.PACKET_AVAILABLE:
            data = self._recv_buffer[:packet_size]
            self._recv_buffer = self._recv_buffer[packet_size:]
            self._handle_packet(data)

    def _register(self) -> None:
        msg = proto.TDS_SuplaRegisterDevice_E()
        msg.email = self._email.encode()
        msg.auth_key[:] = self._authkey
        msg.guid[:] = self._guid
        msg.name = self._name.encode()
        msg.soft_ver = self._version.encode()
        msg.server_name = self._server.encode()
        msg.flags = 0
        msg.manufacturer_id = 0
        msg.product_id = 0
        if len(self._channels) == 0:
            raise DeviceError("No channels")
        msg.channel_count = len(self._channels)
        for number, channel in enumerate(self._channels):
            msg.channels[number].number = number
            msg.channels[number].type = channel.type
            msg.channels[number].action_trigger_caps = channel.action_trigger_caps
            msg.channels[number].default = channel.default
            msg.channels[number].flags = channel.flags
            msg.channels[number].value = ctypes.c_uint64.from_buffer_copy(
                channel.encoded_value
            )
        size = ctypes.sizeof(msg) - (
            (proto.SUPLA_CHANNELMAXCOUNT - msg.channel_count)
            * ctypes.sizeof(proto.TDS_SuplaDeviceChannel_C)
        )
        data = bytes(msg)[:size]

        if self._debug:
            print(
                f"[{self._name}] ---> [{self._rr_id}] registering ({msg.channel_count} channels)"
            )
        self._send_packet(proto.SUPLA_DS_CALL_REGISTER_DEVICE_E, data)

    def _send_ping(self) -> None:
        msg = proto.TDCS_SuplaPingServer()
        now = time.time()
        msg.now.tv_sec = int(now)
        msg.now.tv_usec = int((now - int(now)) * 1000000)
        data = bytes(msg)
        if self._debug:
            print(
                f"[{self._name}] ---> [{self._rr_id}] ping {msg.now.tv_sec},{msg.now.tv_usec}"
            )
        self._send_packet(proto.SUPLA_DCS_CALL_PING_SERVER, data)

    def _send_packet(self, call_id: int, data: bytes) -> None:
        packet = proto.TSuplaDataPacket()
        packet.tag = proto.TAG
        packet.version = proto.SUPLA_PROTO_VERSION
        packet.rr_id = self._rr_id
        packet.call_id = call_id
        packet.data_size = len(data)
        packet.data[:] = data.ljust(ctypes.sizeof(packet.data), b"\x00")

        packet_size = (
            ctypes.sizeof(proto.TSuplaDataPacket)
            - ctypes.sizeof(packet.data)
            + packet.data_size
        )
        packet_data = bytes(packet)[:packet_size] + proto.TAG

        self._socket.write(packet_data)
        self._rr_id += 1

    def _check_for_packet(self) -> tuple[BufferState, int]:
        #  - return INVALID if there is invalid data in the buffer
        #  - if there is a valid packet at the start of the buffer
        #    return PACKET_AVAILABLE and its size
        #  - if there is a valid partial packet at the start of the buffer return INCOMPLETE
        size = len(self._recv_buffer)
        packet_header_size = ctypes.sizeof(proto.TSuplaDataPacket) - (
            ctypes.sizeof(proto.TDS_SuplaDeviceChannel_C) * proto.SUPLA_CHANNELMAXCOUNT
        )

        # check we have enough bytes for a minimally sized packet, followed by end tag
        if size < packet_header_size + len(proto.TAG):
            return BufferState.INCOMPLETE, 0

        # check we have correct start tag
        if self._recv_buffer[: len(proto.TAG)] != proto.TAG:
            return BufferState.INVALID, 0

        # decode packet (possibly partially)
        data = self._recv_buffer
        data += (ctypes.sizeof(proto.TSuplaDataPacket) - len(data)) * b"\x00"
        packet = proto.TSuplaDataPacket.from_buffer_copy(data)

        # check we have correct version
        if packet.version != proto.SUPLA_PROTO_VERSION:
            return BufferState.INVALID, 0

        # check size matches with data size
        expected_size = packet_header_size + packet.data_size + len(proto.TAG)
        if size < expected_size:
            return BufferState.INCOMPLETE, 0

        # check end tag
        if (
            self._recv_buffer[expected_size - len(proto.TAG) : expected_size]
            != proto.TAG
        ):
            return BufferState.INVALID, 0

        # have a complete packet, possibly with more data after
        return BufferState.PACKET_AVAILABLE, expected_size

    def _handle_packet(self, data: bytes) -> None:
        packet_data = data[: -len(proto.TAG)]
        packet_data = packet_data.ljust(ctypes.sizeof(proto.TSuplaDataPacket), b"\x00")
        packet = proto.TSuplaDataPacket.from_buffer_copy(packet_data)
        handlers: dict[int, tuple[Any, Callable[[int, Any], None]]] = {
            proto.SUPLA_SD_CALL_REGISTER_DEVICE_RESULT: (
                proto.TSD_SuplaRegisterDeviceResult,
                self._handle_register_result,
            ),
            proto.SUPLA_CSD_CALL_GET_CHANNEL_STATE: (
                proto.TCSD_ChannelStateRequest,
                self._handle_channel_state_request,
            ),
            proto.SUPLA_SDC_CALL_PING_SERVER_RESULT: (
                proto.TSDC_SuplaPingServerResult,
                self._handle_ping_server_result,
            ),
            proto.SUPLA_SD_CALL_CHANNEL_SET_VALUE: (
                proto.TSD_SuplaChannelNewValue,
                self._handle_channel_new_value,
            ),
        }

        if packet.call_id in handlers:
            struct_type, handler = handlers[packet.call_id]
            result_data = bytes(packet.data)
            result = struct_type.from_buffer_copy(result_data)
            handler(packet.rr_id, result)
        else:
            raise DeviceError(f"Unhandled call {packet.call_id}")

    def _handle_register_result(
        self, rr_id: int, msg: proto.TSD_SuplaRegisterDeviceResult
    ) -> None:
        result_code = proto.SuplaResultCode(msg.result_code)
        if result_code != proto.SuplaResultCode.TRUE:
            raise DeviceError(f"Register failed: {result_code.name}")
        if self._debug:
            print(f"[{self._name}] <--- [{rr_id}] registered ok")
        self._state = DeviceState.CONNECTED

    def _handle_channel_state_request(
        self, rr_id: int, msg: proto.TCSD_ChannelStateRequest
    ) -> None:
        if self._debug:
            print(f"[{self._name}] <--- [{rr_id}] channel state request")

        now = time.time()

        result = proto.TDSC_ChannelState()
        result.receiver_id = msg.sender_id
        result.channel_number = msg.channel_number
        result.padding[:] = b"\x00\x00\x00"
        result.fields = (
            proto.SUPLA_CHANNELSTATE_FIELD_UPTIME
            | proto.SUPLA_CHANNELSTATE_FIELD_CONNECTIONUPTIME
        )
        result.default_icon_field = 0
        result.ipv4 = 0
        result.mac[:] = b"\x00\x00\x00\x00\x00\x00"
        result.battery_level = 0
        result.battery_powered = 0
        result.wifi_rssi = 0
        result.wifi_signal_strength = 0
        result.bridge_node_online = 0
        result.bridge_node_signal_strength = 0
        result.uptime = int(now - self._start_time)
        result.connected_uptime = int(now - self._socket.connect_time)
        result.battery_health = 0
        result.last_connection_reset_cause = 0
        result.light_source_lifespan = 0
        result.light_source_operating_time = 0
        result.empty[:] = b"\x00\x00"

        if self._debug:
            print(f"[{self._name}] ---> [{self._rr_id}] channel state result")
        self._send_packet(proto.SUPLA_DSC_CALL_CHANNEL_STATE_RESULT, bytes(result))

    def _handle_ping_server_result(
        self, rr_id: int, msg: proto.TSDC_SuplaPingServerResult
    ) -> None:
        if self._debug:
            print(
                f"[{self._name}] <--- [{rr_id}] pong {msg.now.tv_sec},{msg.now.tv_usec}"
            )

    def _handle_channel_new_value(
        self, rr_id: int, msg: proto.TSD_SuplaChannelNewValue
    ) -> None:
        if self._debug:
            print(
                f"[{self._name}] <--- [{rr_id}] channel {msg.channel_number} new value"
            )

        success = False
        if msg.channel_number < len(self._channels):
            success = self._channels[msg.channel_number].set_encoded_value(
                bytes(ctypes.c_uint64(msg.value))
            )

        # Note: this sends a SUPLA_DS_CALL_DEVICE_CHANNEL_VALUE_CHANGED_C packet followed
        # by a SUPLA_DS_CALL_CHANNEL_SET_VALUE_RESULT packet. This is swapped compared to
        # the supla linux example client, but still appears to work correctly.

        result = proto.TDS_SuplaChannelNewValueResult()
        result.channel_number = msg.channel_number
        result.sender_id = msg.sender_id
        if success:
            result.success = 1

        if self._debug:
            print(f"[{self._name}] ---> [{self._rr_id}] channel new value result")
        self._send_packet(proto.SUPLA_DS_CALL_CHANNEL_SET_VALUE_RESULT, bytes(result))

    def set_value(self, channel_number: int, value: bytes) -> None:
        if self._state == DeviceState.CONNECTED:
            msg = proto.TDS_SuplaDeviceChannelValue_C()
            msg.channel_number = channel_number
            msg.offline = 0
            msg.validity_time_sec = 0
            msg.value = ctypes.c_uint64.from_buffer_copy(value)
            data = bytes(msg)
            if self._debug:
                print(
                    f"[{self._name}] ---> [{self._rr_id}] channel {channel_number} value changed"
                )
            self._send_packet(proto.SUPLA_DS_CALL_DEVICE_CHANNEL_VALUE_CHANGED_C, data)
