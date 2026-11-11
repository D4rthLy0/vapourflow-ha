"""Constants for the VapourFlow (Autostat / RN4020) Bluetooth fan.

Protocol decoded from the VapourFlow Android app (com.softuvo.vapourflow 1.0).
"""
DOMAIN = "vapourflow"
SERVICE_UUID = "4155544f-5354-4154-8943-5f5f30303031"  # "AUTOSTAT__0001"

# Private RN4020 characteristics; the last 6 bytes spell their name in ASCII.
CHAR_ON32 = "524e3430-3230-4f56-812e-305f4f4e3332"  # status flags (read)
CHAR_ON64 = "524e3430-3230-4f56-812e-305f4f4e3634"  # temperature + humidity (read)
CHAR_IT32 = "524e3430-3230-4f56-812e-305f49543332"  # command register (write, not used yet)

UPDATE_SECONDS = 120  # the fan only answers when asked, and allows one connection at a time
CHAR_IE64 = "524e3430-3230-4f56-812e-305f49453634"
CHAR_IOE08 = "524e3430-3230-4f56-812e-30494f453038"
CHAR_OE64 = "524e3430-3230-4f56-812e-305f4f453634"
CHAR_OT08 = "524e3430-3230-4f56-812e-305f4f543038"
CHAR_OH16 = "524e3430-3230-4f56-812e-305f4f483136"
