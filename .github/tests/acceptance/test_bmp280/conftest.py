import pytest
import time
import subprocess
import serial

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
STARTUP_MSG = "BMP280 connected!"
STARTUP_TIMEOUT = 10.0


def wait_for_startup(ser, expected: str, timeout: float) -> str:
    """Read lines, discarding garbage, until `expected` is found or timeout."""
    deadline = time.monotonic() + timeout
    line = ""
    while time.monotonic() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        if line == expected:
            return line
    raise TimeoutError(
        f"Did not receive {expected!r} within {timeout}s — last line: {line!r}"
    )


@pytest.fixture(scope="function")
def setup_hardware():
    """Open port, reset MCU, and drain garbage until the startup banner arrives."""
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    # No reset_input_buffer — flushing after the reset would discard the startup message.

    subprocess.run(
        [
            "pio",
            "pkg",
            "exec",
            "-p",
            "tool-openocd",
            "-c",
            "openocd -f interface/stlink.cfg -f target/stm32f4x.cfg"
            " -c 'init; reset run; shutdown'",
        ],
        check=True,
    )

    startup_message = wait_for_startup(ser, STARTUP_MSG, STARTUP_TIMEOUT)

    yield ser, startup_message

    ser.close()
