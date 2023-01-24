import pytest
from pysupladevice.device import Device
from pysupladevice.channels import Temperature


@pytest.fixture
def mock_socket(mocker):
    return mocker.patch("pysupladevice.network.Socket")


@pytest.fixture
def mock_channel(mocker):
    return mocker.patch("pysupladevice.channels.Temperature")


def test_device(mock_socket, mock_channel):
    def read():
        # register successful message
        return b"SUPLA\x10\x01\x00\x00\x00F\x00\x00\x00\x07\x00\x00\x00\x03\x00\x00\x00x\x13\x01SUPLA"

    def write(data):
        print(data)

    mock_socket.return_value.read.side_effect = read
    mock_socket.return_value.write.side_effect = write

    device = Device(
        "supla.example.com",
        "email@example.com",
        b"\xaa\x48\xb2\x76\x63\x0a\x3f\xd7\x1a\xdc\xca\xfc\xf0\x08\x9d\xf2",
        b"\x8b\x3f\x59\xf2\x97\xc6\x07\x4f\x1e\xc9\x8a\x25\xce\x14\x78\x5f",
        debug=True,
    )
    channel = Temperature()
    device.add(channel)

    assert device._state == device.State.CONNECTING
    device.loop()
    assert device._state == device.State.REGISTERING
    device.loop()
    assert device._state == device.State.CONNECTED
