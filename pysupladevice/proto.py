import ctypes
from enum import Enum

SUPLA_CHANNELMAXCOUNT = 32

TAG = b"SUPLA"

SUPLA_PROTO_VERSION = 16

SUPLA_DCS_CALL_PING_SERVER = 40
SUPLA_SDC_CALL_PING_SERVER_RESULT = 50
SUPLA_DS_CALL_REGISTER_DEVICE_E = 69
SUPLA_SD_CALL_REGISTER_DEVICE_RESULT = 70
SUPLA_SD_CALL_CHANNEL_SET_VALUE = 110
SUPLA_DS_CALL_CHANNEL_SET_VALUE_RESULT = 120
SUPLA_DS_CALL_DEVICE_CHANNEL_VALUE_CHANGED_C = 103
SUPLA_CSD_CALL_GET_CHANNEL_STATE = 500
SUPLA_DSC_CALL_CHANNEL_STATE_RESULT = 510

SUPLA_GUID_SIZE = 16
SUPLA_SERVER_NAME_MAXSIZE = 65
SUPLA_DEVICE_NAME_MAXSIZE = 201
SUPLA_EMAIL_MAXSIZE = 256
SUPLA_AUTHKEY_SIZE = 16
SUPLA_SOFTVER_MAXSIZE = 21

SUPLA_CHANNELSTATE_FIELD_UPTIME = 0x0080
SUPLA_CHANNELSTATE_FIELD_CONNECTIONUPTIME = 0x0100

SUPLA_CHANNELTYPE_RELAY = 2900
SUPLA_CHANNELTYPE_THERMOMETER = 3034
SUPLA_CHANNELTYPE_HUMIDITYSENSOR = 3036
SUPLA_CHANNELTYPE_HUMIDITYANDTEMPSENSOR = 3038

SUPLA_CHANNEL_FLAG_CHANNELSTATE = 0x00010000

SUPLA_CHANNELFNC_THERMOMETER = 40
SUPLA_CHANNELFNC_HUMIDITY = 42
SUPLA_CHANNELFNC_HUMIDITYANDTEMPERATURE = 45
SUPLA_CHANNELFNC_GENERAL_PURPOSE_MEASUREMENT = 520

SUPLA_TEMPERATURE_NOT_AVAILABLE = -275.0
SUPLA_HUMIDITY_NOT_AVAILABLE = -1

SUPLA_ACTION_CAP_TURN_ON = 0x1
SUPLA_ACTION_CAP_TURN_OFF = 0x2
SUPLA_ACTION_CAP_TOGGLE_x1 = 0x4
SUPLA_ACTION_CAP_TOGGLE_x2 = 0x8
SUPLA_ACTION_CAP_TOGGLE_x3 = 0x10
SUPLA_ACTION_CAP_TOGGLE_x4 = 0x20
SUPLA_ACTION_CAP_TOGGLE_x5 = 0x40


class SuplaResultCode(Enum):
    NONE = 0
    UNSUPORTED = 1
    FALSE = 2
    TRUE = 3
    TEMPORARILY_UNAVAILABLE = 4
    BAD_CREDENTIALS = 5
    LOCATION_CONFLICT = 6
    CHANNEL_CONFLICT = 7
    DEVICE_DISABLED = 8
    ACCESSID_DISABLED = 9
    LOCATION_DISABLED = 10
    CLIENT_DISABLED = 11
    CLIENT_LIMITEXCEEDED = 12
    DEVICE_LIMITEXCEEDED = 13
    GUID_ERROR = 14
    REGISTRATION_DISABLED = 17
    ACCESSID_NOT_ASSIGNED = 18
    AUTHKEY_ERROR = 19
    NO_LOCATION_AVAILABLE = 20
    UNAUTHORIZED = 22
    AUTHORIZED = 23
    NOT_ALLOWED = 24
    CHANNELNOTFOUND = 25
    UNKNOWN_ERROR = 26
    DENY_CHANNEL_BELONG_TO_GROUP = 27
    DENY_CHANNEL_HAS_SCHEDULE = 28
    DENY_CHANNEL_IS_ASSOCIETED_WITH_SCENE = 29
    DENY_CHANNEL_IS_ASSOCIETED_WITH_ACTION_TRIGGER = 30


class SuplaTimeVal(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("tv_sec", ctypes.c_uint64),
        ("tv_usec", ctypes.c_uint64),
    ]


class TActionTriggerProperties(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("related_channel_number", ctypes.c_uint8),
        ("disables_local_operation", ctypes.c_uint32),
    ]


class TDS_SuplaDeviceChannel_C(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("number", ctypes.c_uint8),
        ("type", ctypes.c_int32),
        ("action_trigger_caps", ctypes.c_uint32),
        ("default", ctypes.c_int32),
        ("flags", ctypes.c_int32),
        ("value", ctypes.c_uint64),
    ]


class TDS_SuplaRegisterDevice_E(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("email", ctypes.c_char * SUPLA_EMAIL_MAXSIZE),
        ("auth_key", ctypes.c_byte * SUPLA_AUTHKEY_SIZE),
        ("guid", ctypes.c_byte * SUPLA_GUID_SIZE),
        ("name", ctypes.c_char * SUPLA_DEVICE_NAME_MAXSIZE),
        ("soft_ver", ctypes.c_char * SUPLA_SOFTVER_MAXSIZE),
        ("server_name", ctypes.c_char * SUPLA_SERVER_NAME_MAXSIZE),
        ("flags", ctypes.c_int32),
        ("manufacturer_id", ctypes.c_int16),
        ("product_id", ctypes.c_int16),
        ("channel_count", ctypes.c_uint8),
        ("channels", TDS_SuplaDeviceChannel_C * SUPLA_CHANNELMAXCOUNT),
    ]


class TSD_SuplaRegisterDeviceResult(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("result_code", ctypes.c_int32),
        ("activity_timeout", ctypes.c_int8),
        ("version", ctypes.c_int8),
        ("version_min", ctypes.c_int8),
    ]


class TCSD_ChannelStateRequest(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("sender_id", ctypes.c_int32),
        ("channel_number", ctypes.c_byte),
        ("padding", ctypes.c_byte * 3),
    ]


class TDSC_ChannelState(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("receiver_id", ctypes.c_int32),
        ("channel_number", ctypes.c_byte),
        ("padding", ctypes.c_byte * 3),
        ("fields", ctypes.c_int32),
        ("default_icon_field", ctypes.c_int32),
        ("ipv4", ctypes.c_int32),
        ("mac", ctypes.c_byte * 6),
        ("battery_level", ctypes.c_byte),
        ("battery_powered", ctypes.c_byte),
        ("wifi_rssi", ctypes.c_byte),
        ("wifi_signal_strength", ctypes.c_byte),
        ("bridge_node_online", ctypes.c_byte),
        ("bridge_node_signal_strength", ctypes.c_byte),
        ("uptime", ctypes.c_int32),
        ("connected_uptime", ctypes.c_int32),
        ("battery_health", ctypes.c_byte),
        ("last_connection_reset_cause", ctypes.c_byte),
        ("light_source_lifespan", ctypes.c_int16),
        ("light_source_operating_time", ctypes.c_int32),
        ("empty", ctypes.c_byte * 2),
    ]


class TDCS_SuplaPingServer(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("now", SuplaTimeVal),
    ]


class TSDC_SuplaPingServerResult(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("now", SuplaTimeVal),
    ]


class TSD_SuplaChannelNewValue(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("sender_id", ctypes.c_int32),
        ("channel_number", ctypes.c_byte),
        ("duration_ms", ctypes.c_uint32),
        ("value", ctypes.c_uint64),
    ]


class TDS_SuplaChannelNewValueResult(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("channel_number", ctypes.c_byte),
        ("sender_id", ctypes.c_int32),
        ("success", ctypes.c_char),
    ]


class TDS_SuplaDeviceChannelValue_C(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("channel_number", ctypes.c_byte),
        ("offline", ctypes.c_byte),
        ("validity_time_sec", ctypes.c_uint32),
        ("value", ctypes.c_uint64),
    ]


class TSuplaDataPacket(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("tag", ctypes.c_char * len(TAG)),
        ("version", ctypes.c_uint8),
        ("rr_id", ctypes.c_uint32),
        ("call_id", ctypes.c_uint32),
        ("data_size", ctypes.c_uint32),
        (
            "data",
            ctypes.c_byte
            * (ctypes.sizeof(TDS_SuplaDeviceChannel_C) * SUPLA_CHANNELMAXCOUNT),
        ),
    ]
