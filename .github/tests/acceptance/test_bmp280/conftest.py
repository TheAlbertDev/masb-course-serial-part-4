import pytest
import time
import subprocess
import serial

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200


@pytest.fixture(scope="function")
def setup_hardware():
    """Setup and teardown for BMP280 hardware testing."""
    # Open serial port before reset so the startup message is not lost
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=3)
    ser.reset_input_buffer()

    # Reset the MCU so the program starts from scratch
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
    time.sleep(1.0)  # Wait for MCU init, I2C calibration read, and first measurement

    yield ser

    # Teardown
    ser.close()
