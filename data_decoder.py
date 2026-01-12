import sys
import ctypes
import csv
import os
import json
import sqlite3
import base64
import xml.etree.ElementTree as ET
from colorama import init, Fore, Style
import time
import msvcrt



init()  # Initialize colorama for ANSI colors on Windows


# Globals

# Define available decoders
decode_types = {
    "/xml": "xml",
    "/sql": "sql",
    "/yaml": "yaml",
    "/csv": "csv",
    "/num": "num",
    "/status": "status"
}

valid_num_types = {
    "bin": 2,
    "oct": 8,
    "dec": 10,
    "hex": 16
}

# selected number in.out types
selectednumbers = [None, None]

# decoder per byte toggle
per_byte = True

version = "1.0.4"

# Initialize selected decoder variable
selected = None

# Flag to stop validation loop
stopvalidation = False

# get current directory
current_dir = os.getcwd()

# Config file path
config_file = os.path.join(current_dir, "data_decoder_config.json")

# get arguments
args = sys.argv[1:]

# versions
versions = {
    "alpha1": {
        "data": "unknown",  
        "features": "unknown"
    },

}

# Load config on startup
def load_config():
    global selectednumbers, per_byte
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                selectednumbers = config.get('selectednumbers', [None, None])
                per_byte = config.get('per_byte', True)
        except (json.JSONDecodeError, KeyError):
            pass  # Use defaults if config is corrupted

# Save config on changes
def save_config():
    config = {
        'selectednumbers': selectednumbers,
        'per_byte': per_byte
    }
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass  # Silently fail if can't save

# Load config at start
load_config()


# setup code

print("© 2025 David S all rights reserved.\n")
print(f"Data Decoder App v{version} \n\nAvailable Decoders:\n/xml\n/sql\n/yaml\n/csv\n/num\n")
print("Press Ctrl+C at any time to quit.\nCommands:\nhelp for help in commands,\nexit to exit current mode\nstatus to go into command query mode while in home menu\n")

# If running as EXE and /q passed, hide the console window
if "/q" in args:
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 6)   # 6 = SW_MINIMIZE
for flag, decoder in decode_types.items():
    if flag in args:
        selected = decoder
        break

# prompt user to select a mde
try:
    if selected is None:
        selected = input("Select decoder: ").lower()
except KeyboardInterrupt:
    print("\nProgram interrupted by user. Exiting...")
    sys.exit(0)


# helper function definitions

def move_up(n=1):
    sys.stdout.write(f"\033[{n}A")

def clear_line():
    sys.stdout.write("\033[2K")

def build_debug_table():
    return [
        f"{Fore.CYAN + Style.BRIGHT}=== DEBUG STATUS ==={Style.RESET_ALL}",
        f"arguments     : {args}",
        f"Per-byte mode : {'ON' if per_byte else 'OFF'}",
        f"Input type    : {selectednumbers[0]}",
        f"Output type   : {selectednumbers[1]}",
        f"Time          : {time.strftime('%H:%M:%S')}",
        f"current dir   : {current_dir}",
        f"version       : v{version}",
        "-" * 30
    ]

# pase value function
def parse_value(value):
    value = value.strip()

    if value == "":
        return None

    if value.lower() == "null":
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    if value.isdigit():
        return int(value)

    try:
        return float(value)
    except ValueError:
        pass

    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    return value


# main functions for decoding data

# XML Decoder
def extract_text_from_xml(input_file, output_file):
    try:
        # Parse the XML file
        tree = ET.parse(input_file)
        root = tree.getroot()

        # Recursive function to gather all text
        def get_text(element, depth=0):
            text_content = ""

            if element.text and element.text.strip():
                text_content += ("  " * depth) + element.text.strip() + "\n"

            for child in element:
                text_content += get_text(child, depth + 1)

            if element.tail and element.tail.strip():
                text_content += element.tail.strip() + "\n"

            return text_content

        full_text = get_text(root)

        # Write the text to a new file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_text.strip())

        print(f"Decoded text saved to: {output_file}")

    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    except FileNotFoundError:
        print(f"File not found: {input_file}")

# CSV decoder
def decode_csv(input_file, output_file, column):
    try:
        # Open CSV file
        with open(input_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Check if the requested column exists in the CSV header
            if column not in reader.fieldnames:
                raise KeyError(f"Column '{column}' not found in CSV file.")

            # Write to output
            with open(output_file, "w", encoding="utf-8") as txtfile:
                for row in reader:
                    value = row[column].strip()
                    if value:
                        txtfile.write(value + "\n")

        print(f"CSV column '{column}' decoded to: {output_file}")

    except KeyError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print(f"File not found: {input_file}")
    except csv.Error as e:
        print(f"CSV parsing error: {e}")

# db/sqlite decoder
def decode_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    result = {
        "tables": {}
    }

    # get table names
    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)

    tables = [row["name"] for row in cur.fetchall()]

    for table in tables:
        # get columns
        cur.execute(f"PRAGMA table_info({table})")
        columns = cur.fetchall()

        column_info = [
            {
                "name": col["name"],
                "type": col["type"]
            }
            for col in columns
        ]

        # fetch rows
        cur.execute(f"SELECT * FROM {table}")
        rows = []

        for row in cur.fetchall():
            record = {}
            for key in row.keys():
                value = row[key]

                # handle blobs
                if isinstance(value, bytes):
                    value = {
                        "__type__": "blob",
                        "base64": base64.b64encode(value).decode("ascii")
                    }

                record[key] = value

            rows.append(record)

        result["tables"][table] = {
            "columns": column_info,
            "rows": rows
        }

    conn.close()
    return result

# YAML decoder
def decode_yaml(lines):
    root = {}
    stack = [(-1, root)]

    for raw_line in lines:
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        line = line.lstrip()

        while indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        # list item
        if line.startswith("- "):
            value_part = line[2:].strip()

            if not isinstance(parent, list):
                new_list = []
                stack[-1] = (stack[-1][0], new_list)

                container = stack[-2][1]
                for k in reversed(container):
                    if container[k] == {}:
                        container[k] = new_list
                        break

                parent = new_list

            if ":" in value_part:
                item = {}
                parent.append(item)
                stack.append((indent, item))

                key, value = value_part.split(":", 1)
                item[key.strip()] = parse_value(value.strip())
            else:
                parent.append(parse_value(value_part))

            continue

        # key / value
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if value == "":
                parent[key] = {}
                stack.append((indent, parent[key]))
            else:
                parent[key] = parse_value(value)

    return root

# number covert num type in num type out function
def convertnum(value, type_out, type_in, per_byte):
    try:
        if type_out not in valid_num_types or type_in not in valid_num_types:
            print("Invalid number type specified.")
            return None

        base_in = valid_num_types[type_in]
        base_out = valid_num_types[type_out]

        if not per_byte:
            num = int(value, base_in)
            return format(num, {
                "bin": "b",
                "oct": "o",
                "dec": "d",
                "hex": "x"
            }[type_out])

        # =========================
        # PER-BYTE MODE
        # =========================
        # Split input by spaces to support files like "00 FF 0A ..."
        parts = value.strip().split() if " " in value.strip() else [value.strip()]
        byte_values = []
        for part in parts:
            if type_in == "hex":
                byte_values.append(int(part, 16))
            elif type_in == "bin":
                byte_values.append(int(part, 2))
            elif type_in == "oct":
                byte_values.append(int(part, 8))
            elif type_in == "dec":
                byte_values.append(int(part, 10))
            else:
                raise ValueError("Unsupported input type")

        # Convert each byte to output format
        output = []
        for b in byte_values:
            fmt = {"bin": "08b", "oct": "03o", "dec": "d", "hex": "02x"}[type_out]
            output.append(format(b, fmt))

        return " ".join(output)

    except ValueError as e:
        print(f"Invalid number value: {e}")
        return None


# Main prompt selection logic
try:
    while True:
        if (selected is not None and selected not in decode_types.values()) and selected not in ("status", "debug"):
            print("Invalid decoder selected. Please choose from the available options.")
            selected = input("Select decoder: ").lower()
        elif selected is None:
            # Just prompt silently
            selected = input("Select decoder: ").lower()
        elif not stopvalidation:
            print(f'selected decoder is valid. {selected}')
            stopvalidation = True
        

        # if selected blocks
        if selected == "xml":
            print("XML decoder mode. Type: decode <file.xml> or exit")

            while True:
                try:
                    command = input("> ").strip()
                except KeyboardInterrupt:
                    print("\nExiting XML mode.")
                    break

                if not command:
                    continue

                if command.lower() == "help":
                    print("Commands:\n decode <file.xml> - Decode the specified XML file\n exit - Exit XML mode")
                    continue

                if command.lower() == "exit":
                    selected = None
                    stopvalidation = False
                    print("Exiting XML mode.")
                    break

                if command.lower().startswith("decode "):
                    input_file = command[7:].strip().strip('"')

                    base_name = os.path.splitext(input_file)[0]
                    output_file = base_name + "_decoded.txt"

                    extract_text_from_xml(input_file, output_file)
                    continue

                print("Unknown command. Type 'help' for options.")

        elif selected == "csv":
            while True:
                try:
                    command = input("> ").strip()
                except KeyboardInterrupt:
                    print("\nExiting CSV mode.")
                    break
                if not command:
                    continue

                if command.lower() == "help":
                    print("Commands:\n decode <file.csv> <column_name> - Decode the specified CSV file column\n exit - Exit CSV mode")
                    continue

                if command.lower().startswith("decode "):
                    parts = command[7:].strip().split(" ", 1)
                    if len(parts) != 2:
                        print("Invalid command format. Use: decode <file.csv> <column_name>")
                        continue

                    input_file = parts[0].strip().strip('"')
                    column_name = parts[1].strip().strip('"')

                    base_name = os.path.splitext(input_file)[0]
                    output_file = base_name + f"_{column_name}_decoded.txt"

                    decode_csv(input_file, output_file, column_name)
                    continue

                if command.lower() == "exit":
                    selected = None
                    stopvalidation = False
                    print("Exiting XML mode.")
                    break

        elif selected == "sql":
            while True:
                try:
                    command = input("> ").strip()
                except KeyboardInterrupt:
                    print("\nExiting SQL mode.")
                    break

                if not command:
                    continue

                if command.lower() == "help":
                    print("Commands:\n decode <file.sqlite> - Decode the specified SQLite database file\n exit - Exit SQL mode")
                    continue

                if command.lower() == "exit":
                    selected = None
                    stopvalidation = False
                    print("Exiting SQL mode.")
                    break

                if command.lower().startswith("decode "):
                    input_file = command[7:].strip().strip('"')

                    output_file = input_file + ".decoded.json"

                    data = decode_sqlite(input_file)

                    with open(output_file, "w", encoding="utf-8") as out:
                        json.dump(
                            data,
                            out,
                            indent=2,
                            sort_keys=True
                        )

                    print("Decoded SQLite DB written to:", output_file)
                    continue

        elif selected == "yaml":
            while True:
                try:
                    command = input("> ").strip()
                except KeyboardInterrupt:
                    print("\nExiting YAML mode.")
                    break

                if not command:
                    continue

                if command.lower() == "help":
                    print("Commands:\n decode <file.yaml> - Decode the specified YAML file\n exit - Exit YAML mode")
                    continue

                if command.lower() == "exit":
                    selected = None
                    stopvalidation = False
                    print("Exiting YAML mode.")
                    break

                if command.lower().startswith("decode "):
                    input_file = command[7:].strip().strip('"')

                    output_file = input_file + ".decoded.json"

                    with open(input_file, "r", encoding="utf-8") as f:
                        data = decode_yaml(f.readlines())

                    with open(output_file, "w", encoding="utf-8") as out:
                        json.dump(
                            data,
                            out,
                            indent=2,          # pretty formatting
                            sort_keys=True     # deterministic ordering
                        )

                    print("Decoded YAML written to:", output_file)
                    continue

        elif selected == "num":
            while True:
                try:
                    command = input("> ").strip()
                except KeyboardInterrupt:
                    print("\nExiting Number Conversion mode.")
                    break
                if not command:
                    continue

                if command.lower() == "help":
                    print("Commands:\n setin <type> - Set input number type (bin, oct, dec, hex)\n setout <type> - Set output number type (bin, oct, dec, hex)\n convert <file> - Convert the number from input type to output type\n exit - Exit Number Conversion mode\n status - Show current settings\n toggleperbyte - Toggle per-byte mode ON/OFF")
                    continue

                if command.lower() == "status":
                    print(f"Per-byte mode: {'ON' if per_byte else 'OFF'}")
                    print(f"Input type: {selectednumbers[0]}")
                    print(f"Output type: {selectednumbers[1]}")
                    continue

                if command.lower() == "toggleperbyte":
                    per_byte = not per_byte
                    print(f"Per-byte mode set to: {'ON' if per_byte else 'OFF'}")
                    save_config()  # Save settings
                    continue

                if command.lower() == "exit":
                    selected = None
                    stopvalidation = False
                    print("Exiting Number Conversion mode.")
                    break

                if command.lower().startswith("setin "):
                    type_in = command[6:].strip().lower()
                    if type_in in valid_num_types:
                        selectednumbers[0] = type_in
                        print(f"Input number type set to: {type_in}")
                        save_config()  # Save settings
                    else:
                        print("Invalid number type. Valid types are: bin, oct, dec, hex.")
                    continue

                if command.lower().startswith("setout "):
                    type_out = command[7:].strip().lower()
                    if type_out in valid_num_types:
                        selectednumbers[1] = type_out
                        print(f"Output number type set to: {type_out}")
                        save_config()  # Save settings
                    else:
                        print("Invalid number type. Valid types are: bin, oct, dec, hex.")
                    continue

                if command.lower().startswith("convert "):
                    input_value = command[8:].strip()
                    if selectednumbers[0] is None or selectednumbers[1] is None:
                        print("Please set both input and output number types before converting.")
                        continue

                    # If input is a file, read it
                    if os.path.isfile(input_value):
                        with open(input_value, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        output_lines = []
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            result = convertnum(line, selectednumbers[1], selectednumbers[0], per_byte)
                            if result is not None:
                                output_lines.append(result)
                            else:
                                print(f"Failed to convert line: {line}")
                        if not output_lines:
                            print("No valid values were converted. Output file was not created.")
                            continue

                        # Write to output file
                        base_name = os.path.splitext(input_value)[0]
                        output_file = base_name + "_decoded.txt"
                        with open(output_file, "w", encoding="utf-8") as out:
                            out.write("\n".join(output_lines))
                        print(f"Converted value saved to: {output_file}")

                    else:
                        # direct input
                        result = convertnum(input_value, selectednumbers[1], selectednumbers[0], per_byte)
                        if result is not None:
                            print(f"Converted value: {result}")
        elif selected == "status":
            print(f"{Fore.GREEN + Style.BRIGHT}status: menu mode. Type 'help' for commands or 'exit' to leave status mode.")
            try:
                while True:
                    command = input("> ").strip()
                    if not command:
                        continue

                    if command.lower() == "help":
                        print("Commands:\n   exit - Exit status mode\n   dir - List files in current directory\n   pwd - Show current directory path\n   read <file> - Read and display contents of a file\n   debug - opens debug menu\n   clear - Clear the screen")
                        continue

                    if command.lower() == "exit":
                        print(Style.RESET_ALL + "Exiting status mode.")
                        selected = None
                        stopvalidation = False
                        break
                        
                    if command.lower() == "dir":
                        files = os.listdir(current_dir)
                        print("Files in current directory:")
                        for f in files:
                            print(f"  {f}")
                        continue

                    if command.lower() == "pwd":
                        print(f"Current directory: {current_dir}")
                        continue

                    if command.lower().startswith("read "):
                        file_to_read = command[5:].strip().strip('"')
                        full_path = os.path.join(current_dir, file_to_read)
                        try:
                            with open(full_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            print(f"Contents of {file_to_read}:\n")
                            print(content)
                        except FileNotFoundError:
                            print(f"File not found: {file_to_read}")
                        except Exception as e:
                            print(f"Error reading file: {e}")
                        continue
                    
                    if command.lower() == "debug":
                        selected = "debug"
                        stopvalidation = False
                        break

                    if command.lower() == "clear":
                        os.system('cls' if os.name == 'nt' else 'clear')
                        continue

                    
            except KeyboardInterrupt:
                print("\nExiting status mode.")
                selected = None
                stopvalidation = False
        elif selected == "debug":
            print("warning if you use in valid commands like spaming viberish his will break")
            print("Entering debug mode. Type 'exit' to return.\n")

            debug_lines = []
            debug_lines_count = 0

            buffer = ""
            last_update = 0

            try:
                while True:
                    now = time.time()

                    # Redraw every second
                    if now - last_update >= 1:
                        lines = build_debug_table()

                        move_up(debug_lines_count)
                        for _ in range(debug_lines_count):
                            clear_line()
                            print()
                        move_up(debug_lines_count)

                        for line in lines:
                            print(line)

                        debug_lines_count = len(lines)
                        last_update = now

                        # Reprint input line
                        clear_line()
                        sys.stdout.write("> " + buffer)
                        sys.stdout.flush()

                    # Non-blocking keyboard input
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()

                        if ch == "\r":  # Enter
                            command = buffer.strip()
                            buffer = ""
                            print()  # move to next line

                            if command.lower() == "exit":
                                move_up(debug_lines_count)
                                for _ in range(debug_lines_count):
                                    clear_line()
                                    print()
                                move_up(debug_lines_count)

                                print("Exited debug mode.")
                                selected = None
                                stopvalidation = False
                                break
                            elif command:
                                print(f"Debug command received: {command}")

                            sys.stdout.write("> ")
                            sys.stdout.flush()

                        elif ch == "\b":  # Backspace
                            buffer = buffer[:-1]
                            clear_line()
                            sys.stdout.write("> " + buffer)
                            sys.stdout.flush()

                        else:
                            buffer += ch
                            sys.stdout.write(ch)
                            sys.stdout.flush()

                    time.sleep(0.05)

            except KeyboardInterrupt:
                print("\nExiting debug mode.")
                selected = None
                stopvalidation = False




except KeyboardInterrupt:
    print("\nProgram interrupted by user. Exiting...")
    sys.exit(0)