# Portions of this file are derived from the PerimeterX-Solver project
# Source: https://github.com/Pr0t0ns/PerimeterX-Solver (solve.py)
#
# Copyright (C) Pr0t0ns
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See LICENSE

import json
import time
import uuid
import base64
import re
import random
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from utils.px_utils import generate_pc


class WalmartPXGenerator:
    def __init__(
        self,
        app_id: str,
        ft: int,
        collector_uri: str,
        host: str,
        sid: str,
        vid: str,
        cts: str,
    ):
        self.base_url = host
        self.host = host
        self.app_id = app_id
        self.tag = "v6.7.9"
        self.ft = ft
        self.collector_uri = collector_uri
        self.sid = sid
        self.vid = vid
        self.cts = cts

    def _encode(self, payload: str, e: int = 50) -> str:
        output = ""
        for i in range(len(payload)):
            output += chr(ord(payload[i]) ^ e)
        return output

    def _encrypt(self, payload: str) -> str:
        quoted = quote(payload)
        decoded = re.sub(r"%([0-9A-F]{2})", lambda m: chr(int(m.group(1), 16)), quoted)
        return base64.b64encode(decoded.encode()).decode()

    def _encrypt_payload(self, payload: str) -> str:
        # XOR then percent-decode+base64, matching  solver's encode_string flow
        return self._encrypt(self._encode(payload))

    def _generate_fingerprint_1(self, host: str, uuid: str, st: int):
        return json.dumps(
            (
                [
                    {
                        "t": "PX2",
                        "d": {
                            "PX96": host,
                            "PX63": "Win32",
                            "PX191": 0,
                            "PX850": 0,
                            "PX851": random.randint(300, 700),
                            "PX1008": 3600,
                            "PX1055": st,
                            "PX1056": st + random.randint(1, 50),
                            "PX1038": uuid,
                            "PX371": False,
                        },
                    }
                ]
            ),
            separators=(",", ":"),
        )

    def _generate_fingerprint_2(
        self, payload_1_json: list, response_do: str, vid: str, sid: str
    ):
        # Source: https://github.com/Pr0t0ns/PerimeterX-Solver (fingerprint.py)
        payload_1 = payload_1_json[0]["d"]
        response_data = str(response_do)

        def fn(t, n):
            return self._encode(t, n)

        def gen_pc_wrap(ua, val):
            # fingerprint.py uses a hardcoded UA for generate_pc calls inside the dict
            # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            return generate_pc(ua, val, False)

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

        pst = timezone(timedelta(hours=-7))
        formatted_date = (
            datetime.now(pst).strftime("%a %b %d %Y %H:%M:%S GMT%z")
            + " (Pacific Daylight Time)"
        )

        def safe_split(s, key):
            try:
                return s.split(key)[1].split("',")[0]
            except IndexError:
                return "0"

        cls_val = safe_split(response_data, "cls|")
        sts_val = int(safe_split(response_data, "sts|"))
        drc_val = int(safe_split(response_data, "drc|"))
        wcs_val = safe_split(response_data, "wcs|")

        key_dynamic = f"{fn(cls_val, sts_val % 10 + 2)}"
        val_dynamic = f"{fn(cls_val, sts_val % 10 + 1)}"

        fp = [
            {
                "t": "PX3",
                "d": {
                    "PX234": False,
                    "PX235": False,
                    "PX151": False,
                    "PX239": False,
                    "PX240": False,
                    "PX152": False,
                    "PX153": False,
                    "PX314": False,
                    "PX192": False,
                    "PX196": False,
                    "PX207": False,
                    "PX251": False,
                    "PX982": sts_val,
                    "PX983": cls_val,
                    key_dynamic: val_dynamic,
                    "PX985": drc_val,
                    "PX1033": "49e5084e",
                    "PX1019": "1530fd3",
                    "PX1020": "57b9b686",
                    "PX1021": "180dd7e3",
                    "PX1022": "6a90378d",
                    "PX1035": True,
                    "PX1139": False,
                    "PX1025": False,
                    "PX359": f"{generate_pc(ua, payload_1['PX1038'], False)}",
                    "PX943": wcs_val,
                    "PX357": f"{generate_pc(ua, vid, False)}",
                    "PX358": f"{generate_pc(ua, sid, False)}",
                    "PX229": 24,
                    "PX230": 24,
                    "PX91": 1280,
                    "PX92": 800,
                    "PX269": 1280,
                    "PX270": 752,
                    "PX93": "1280X800",
                    "PX185": 665,
                    "PX186": 252,
                    "PX187": 0,
                    "PX188": 0,
                    "PX95": True,
                    "PX400": 1441,
                    "PX404": "109|66|66|70|80",
                    "PX90": ["loadTimes", "csi", "app"],
                    "PX190": "",
                    "PX552": "false",
                    "PX399": "false",
                    "PX549": 1,
                    "PX411": 1,
                    "PX405": True,
                    "PX547": True,
                    "PX134": True,
                    "PX89": True,
                    "PX170": 5,
                    "PX85": [
                        "PDF Viewer",
                        "Chrome PDF Viewer",
                        "Chromium PDF Viewer",
                        "Microsoft Edge PDF Viewer",
                        "WebKit built-in PDF",
                    ],
                    "PX1179": True,
                    "PX1180": True,
                    "PX59": ua,
                    "PX61": "en-US",
                    "PX313": ["en-US", "en"],
                    "PX63": payload_1["PX63"],
                    "PX86": True,
                    "PX154": 420,
                    "PX1157": 8,
                    "PX1173": 2,
                    "PX133": True,
                    "PX88": True,
                    "PX169": 2,
                    "PX62": "Gecko",
                    "PX69": "20030107",
                    "PX64": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                    "PX65": "Netscape",
                    "PX66": "Mozilla",
                    "PX1144": True,
                    "PX1152": 1.45,
                    "PX1153": 100,
                    "PX1154": False,
                    "PX1155": "4g",
                    "PX60": True,
                    "PX87": True,
                    "PX821": 4294705152,
                    "PX822": 21869834,
                    "PX823": 18631122,
                    "PX147": False,
                    "PX155": formatted_date,
                    "PX236": False,
                    "PX194": False,
                    "PX195": True,
                    "PX237": 10,
                    "PX238": "missing",
                    "PX208": "visible",
                    "PX218": 0,
                    "PX231": 752,
                    "PX232": 1280,
                    "PX254": False,
                    "PX295": False,
                    "PX268": False,
                    "PX166": True,
                    "PX138": False,
                    "PX143": True,
                    "PX1142": 8,
                    "PX1143": 3,
                    "PX1146": 0,
                    "PX1147": 1,
                    "PX714": "64556c77",
                    "PX715": "",
                    "PX724": "10207b2f",
                    "PX725": "10207b2f",
                    "PX729": "90e65465",
                    "PX443": True,
                    "PX466": True,
                    "PX467": True,
                    "PX468": True,
                    "PX191": payload_1["PX191"],
                    "PX94": 6,
                    "PX120": [],
                    "PX141": False,
                    "PX96": payload_1["PX96"],
                    "PX55": quote(str(payload_1["PX96"]), safe=""),
                    "PX34": "Error\\n    at Oe (https://static.airtable.com/js/lib/perimeterx/v1/PX0OZADU9K/init.js:3:10744)\\n    at ye (https://static.airtable.com/js/lib/perimeterx/v1/PX0OZADU9K/init.js:3:1750)",
                    "PX1065": 2,
                    "PX850": payload_1["PX850"],
                    "PX851": payload_1["PX851"],
                    "PX1054": int(time.time()) * 1000,
                    "PX1008": payload_1["PX1008"],
                    "PX1055": payload_1["PX1055"],
                    "PX1056": payload_1["PX1056"],
                    "PX1038": payload_1["PX1038"],
                    "PX371": payload_1["PX371"],
                },
            }
        ]

        json_str = json.dumps(fp, separators=(",", ":"))
        return (
            json_str.replace(r"\n", "\\n")
            .replace(r")\n", r")\\n")
            .replace(r"r\n", r"r\\n")
            .replace(r"Error\n", r"Error\\n")
        )

    #  Generate initial payload (PX2) for v2 collector
    def generate_payload(self, px_uid: str = None):
        current_time = int(time.time() * 1000)
        if not px_uid:
            px_uid = str(uuid.uuid4())

        # PX2 structure
        raw_payload_str = self._generate_fingerprint_1(
            self.base_url, px_uid, current_time
        )

        # Use unpadded encryption for v2
        encrypted_payload = self._encrypt_payload(raw_payload_str)

        # Solver metadata
        pc_key = f"{px_uid}:{self.tag}:{self.ft}"

        data = {
            "payload": encrypted_payload,
            "appId": self.app_id,
            "tag": self.tag,
            "uuid": px_uid,
            "ft": self.ft,
            "seq": 0,
            "en": "NTA",
            "pc": generate_pc(pc_key, raw_payload_str),
            "sid": self.sid,
            "vid": self.vid,
            "cts": self.cts,
            "rsc": 1,
        }

        # Return data dict, raw payload (as list for step 2), px_uid
        # _generate_fingerprint_1 returns a JSON string of a list
        return data, json.loads(raw_payload_str), px_uid

    def generate_challenge_payload(
        self,
        raw_payload_1,
        response_do,
        px_uid,
        seq=1,
        sid: str = "",
        vid: str = "",
        cts: str = "",
    ):
        payload_1_list = None
        if raw_payload_1:
            try:
                if isinstance(raw_payload_1, str):
                    payload_1_list = json.loads(raw_payload_1)
                else:
                    payload_1_list = raw_payload_1
            except Exception:
                payload_1_list = None

        # Fallback shim if payload_1 is missing or malformed
        if not payload_1_list or not isinstance(payload_1_list, list):
            payload_1_list = [
                {
                    "d": {
                        "PX63": "Win32",
                        "PX1038": px_uid,
                        "PX96": self.base_url,
                        "PX191": 0,
                        "PX850": 0,
                        "PX851": 0,
                        "PX1008": 3600,
                        "PX1055": int(time.time() * 1000),
                        "PX1056": int(time.time() * 1000),
                        "PX371": True,
                    }
                }
            ]

        fp2 = self._generate_fingerprint_2(payload_1_list, response_do, vid, sid)

        pc_key = f"{px_uid}:{self.tag}:{self.ft}"

        try:
            cs_val = str(response_do).split("cs|")[1].split("',")[0]
        except:
            cs_val = ""

        data = {
            "payload": self._encrypt_payload(fp2),
            "appId": self.app_id,
            "tag": self.tag,
            "uuid": px_uid,
            "ft": self.ft,
            "seq": seq,
            "en": "NTA",
            "cs": cs_val,
            "pc": generate_pc(pc_key, fp2),
            "sid": sid,
            "vid": vid,
            "cts": cts,
            "rsc": seq + 1,
        }

        return data
