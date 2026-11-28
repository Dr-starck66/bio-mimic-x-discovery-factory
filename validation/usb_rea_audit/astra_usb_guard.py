"""Read-only validation boundary for usb-rea 0.7.14; no device access.
Initial policy: one bus per capture; no truncated transfer records.
This does not validate all pcap/pcapng container invariants or authorize actuation.
"""
import struct
from usb_rea.pcap import iter_packets, read_transfers, find_ids

class CaptureRejected(ValueError):
    pass

def guarded_read(path):
    buses=set()
    for frame, ts, lt, raw in iter_packets(path):
        if lt in (189,220):
            header=48 if lt==189 else 64
            if len(raw)<header:
                raise CaptureRejected(f'frame {frame}: short USB header')
            bus=struct.unpack_from('<H',raw,12)[0]
            declared=struct.unpack_from('<I',raw,36)[0]
        elif lt==249:
            if len(raw)<27:
                raise CaptureRejected(f'frame {frame}: short USBPcap header')
            header=struct.unpack_from('<H',raw,0)[0]
            bus=struct.unpack_from('<H',raw,17)[0]
            declared=struct.unpack_from('<I',raw,23)[0]
            if header<27:
                raise CaptureRejected(f'frame {frame}: invalid USBPcap header length')
        else:
            raise CaptureRejected(f'frame {frame}: unsupported link type {lt}')
        if len(raw)<header+declared:
            raise CaptureRejected(f'frame {frame}: incomplete record')
        buses.add(bus)
        if len(buses)>1:
            raise CaptureRejected('mixed buses: split and validate independently')
    # Intended for immutable offline inputs; not a live-file or untrusted parser sandbox.
    return read_transfers(path)

def guarded_ids(path):
    return find_ids(guarded_read(path))
