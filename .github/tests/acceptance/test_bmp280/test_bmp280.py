import re

TEMP_MIN = 0.0
TEMP_MAX = 50.0
PRESS_MIN = 85000.0
PRESS_MAX = 110000.0

DATA_LINE_PATTERN = re.compile(r"^T:\s*([-\d.]+),\s*P:\s*([-\d.]+)$")


def read_line(ser):
    line = ser.readline().decode("utf-8", errors="replace").strip()
    assert line, "Received empty line (possible timeout or disconnection)"
    return line


def test_bmp280_startup_message(setup_hardware):
    ser = setup_hardware
    startup = read_line(ser)
    assert startup == "BMP280 connected!", \
        f"Expected 'BMP280 connected!', got {startup!r}"


def test_bmp280_data_format(setup_hardware):
    ser = setup_hardware
    read_line(ser)  # skip startup message
    data = read_line(ser)
    assert DATA_LINE_PATTERN.match(data), \
        f"Data line does not match 'T: <float>, P: <float>', got {data!r}"


def test_bmp280_temperature_in_range(setup_hardware):
    ser = setup_hardware
    read_line(ser)  # skip startup message
    data = read_line(ser)
    m = DATA_LINE_PATTERN.match(data)
    assert m, f"Line format error: {data!r}"
    temperature = float(m.group(1))
    assert TEMP_MIN <= temperature <= TEMP_MAX, \
        f"Temperature {temperature} °C is out of expected range [{TEMP_MIN}, {TEMP_MAX}]"


def test_bmp280_pressure_in_range(setup_hardware):
    ser = setup_hardware
    read_line(ser)  # skip startup message
    data = read_line(ser)
    m = DATA_LINE_PATTERN.match(data)
    assert m, f"Line format error: {data!r}"
    pressure = float(m.group(2))
    assert PRESS_MIN <= pressure <= PRESS_MAX, \
        f"Pressure {pressure} Pa is out of expected range [{PRESS_MIN}, {PRESS_MAX}]"


def test_bmp280_readings_consistency(setup_hardware):
    ser = setup_hardware
    read_line(ser)  # skip startup message

    temperatures, pressures = [], []
    for _ in range(3):
        data = read_line(ser)
        m = DATA_LINE_PATTERN.match(data)
        assert m, f"Line format error: {data!r}"
        temperatures.append(float(m.group(1)))
        pressures.append(float(m.group(2)))

    temp_spread = max(temperatures) - min(temperatures)
    press_spread = max(pressures) - min(pressures)
    assert temp_spread < 5.0, \
        f"Temperature readings too inconsistent (spread: {temp_spread:.2f} °C): {temperatures}"
    assert press_spread < 500.0, \
        f"Pressure readings too inconsistent (spread: {press_spread:.2f} Pa): {pressures}"
