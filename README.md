# Data Decoder App

**Version:** 1.0.4  
**Author:** David S  
**Copyright:** © 2026 David S all rights reserved      

---

## Overview

**Data Decoder App** is an interactive command-line utility for decoding, extracting, converting, and inspecting data from multiple formats.

Supported formats include XML, CSV, SQLite databases, YAML, and numeric base conversions.  
The application also provides a status shell and a live debug interface.

Key goals:
- Interactive CLI
- Multiple decoder modes
- Persistent configuration
- Windows compatibility with ANSI colors

---

## Supported Decoders

| Decoder | Description |
|------|------------|
| `/xml` | Extracts readable text from XML files |
| `/csv` | Extracts values from a specific CSV column |
| `/sql` | Converts SQLite databases into JSON |
| `/yaml` | Parses YAML into structured JSON |
| `/num` | Converts numbers between bases |
| `status` | File system & environment inspection |
| `debug` | Live internal state display |

---

## Installation

Python 3.8+ is recommended.

Install dependencies:
```bash
pip install colorama
```

---

## License

datadecoder - A small python app for decoding data
Copyright (C) 2026 PenguineDavid

This program is free software: you can redistribute it and/or modify  
it under the terms of the GNU General Public License as published by  
the Free Software Foundation, either version 3 of the License, or  
(at your option) any later version.

See the [LICENSE](https://github.com/PenguineDavid/datadecoder?tab=GPL-3.0-1-ov-file) file for the full license text.