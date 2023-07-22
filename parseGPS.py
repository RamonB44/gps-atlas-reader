import serial, os, json, sys


def parse_gpgga(sentence):
    data = sentence.split(",")
    # print(data)
    if data[0] == "$GPGGA":
        time = data[1]
        latitude_degrees, latitude_minutes, _ = split_degrees_minutes(data[2])
        longitude_degrees, longitude_minutes, _ = split_degrees_minutes(data[4])
        gps_quality = int(data[6])
        num_satellites = int(data[7])
        hdop = float(data[8])
        altitude = float(data[9])
        geoid_height = float(data[11]) if data[11] else None
        return {
            "time": time,
            "latitude": f"{latitude_degrees} {latitude_minutes}"
            if data[3] == "N"
            else f"-{latitude_degrees} {latitude_minutes}",
            "longitude": f"{longitude_degrees} {longitude_minutes}"
            if data[5] == "E"
            else f"-{longitude_degrees} {longitude_minutes}",
            "gps_quality": gps_quality,
            "num_satellites": num_satellites,
            "hdop": hdop,
            "altitude": altitude,
            "geoid_height": geoid_height,
        }
    return None


def parse_gpvtg(sentence):
    data = sentence.split(",")
    # print(data)
    if data[0] == "$GPVTG":
        # print(data[5])
        speed_knots = float(data[5]) if data[5] else None
        speed_kmh = float(data[7]) if data[7] else None
        return {"speed_knots": speed_knots, "speed_kmh": speed_kmh}
    return None


def parse_nmea_sentences(sentences):
    parsed_data = []
    for sentence in sentences:
        if sentence.startswith("$GPGGA"):
            data = parse_gpgga(sentence)
            if data:
                parsed_data.append(data)
        elif sentence.startswith("$GPVTG"):
            data = parse_gpvtg(sentence)
            if data:
                if (
                    parsed_data
                ):  # Check if there is a GPGGA sentence before adding GPVTG data
                    parsed_data[-1].update(data)
    return parsed_data


def validate_checksum(sentence):
    # Extract the sentence and the provided checksum from the input
    sentence = sentence.strip()
    if sentence.startswith("$"):
        sentence = sentence[1:]
    parts = sentence.split("*")
    if len(parts) != 2:
        return False

    data = parts[0]
    provided_checksum = parts[1]

    # Calculate the expected checksum
    expected_checksum = 0
    for char in data:
        expected_checksum ^= ord(char)

    # Convert the provided checksum to an integer
    try:
        provided_checksum = int(provided_checksum, 16)
    except ValueError:
        return False

    # Compare the calculated checksum with the provided checksum
    return expected_checksum == provided_checksum


def split_degrees_minutes(coord_str):
    # Check if the input is in the correct format (e.g., "ddmm.mmmm" for degrees and minutes)
    if not (isinstance(coord_str, str) and len(coord_str) >= 4):
        raise ValueError("Invalid input format. Expected 'ddmm.mmmm'.")

    # Extract the degrees and minutes components
    if coord_str.startswith("0"):
        degrees = int(coord_str[:3])
        minutes = float(coord_str[3:])
    else:
        degrees = int(coord_str[:2])
        minutes = float(coord_str[2:])

    # Combine degrees and minutes to get the full coordinate value
    coordinate = degrees + minutes / 60.0

    return degrees, minutes, coordinate

if __name__ == "__main__":
    try:
        file = open('gps_data.json', 'w')
        atlas_gps = serial.Serial(port="COM9", baudrate=19200)
        nmea_data = []
        file.write("[")
        while True:
            raw_string_b = atlas_gps.readline()
            raw_string_s = raw_string_b.decode("utf-8")
            # print(raw_string_s)
            if raw_string_s.startswith("$GPGGA"):
                nmea_data.insert(0,raw_string_s)
            if raw_string_s.startswith("$GPVTG"):
                nmea_data.insert(1,raw_string_s)
            if len(nmea_data) > 1:
                parsed_data = parse_nmea_sentences(nmea_data)
                file.write(json.dumps(parsed_data[0]))
                file.write(",\n")
                print(parsed_data)
                nmea_data = []
    except:
        file.write("]")
        file.close()
        sys.exit(1)
            
        
