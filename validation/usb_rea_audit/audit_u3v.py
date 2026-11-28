"""Offline audit of the published USB3 Vision sample; no device access."""
import hashlib, json, struct, sys
from collections import Counter
from pathlib import Path
from usb_rea.pcap import read_transfers, find_ids, iter_packets
from astra_usb_guard import guarded_read, CaptureRejected

EXPECTED = 'f278c4178696d4a744e6e2894d08d1211e2f4aa058d0f23c1f9267d7813c2937'

def audit(path):
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if digest != EXPECTED:
        raise ValueError('capture hash mismatch')
    transfers = read_transfers(path)
    ids = find_ids(transfers)
    outs = [t for t in transfers if t.kind == 'bulk' and t.is_out]
    assert ids[19][0] == 0x2676 and len(outs) > 10 and all(t.data[:4] == b'U3VC' for t in outs)
    packets = list(iter_packets(path))
    truncated = []
    for frame, _, lt, raw in packets:
        assert lt == 249 and len(raw) >= 27
        hlen = struct.unpack_from('<H', raw)[0]
        declared = struct.unpack_from('<I', raw, 23)[0]
        if len(raw) < hlen + declared:
            truncated.append({'frame': frame, 'declared': declared, 'captured': max(0,len(raw)-hlen)})
    bulk = [t for t in transfers if t.kind == 'bulk']
    controls = []
    for t in bulk:
        if t.data[:4] == b'U3VC' and len(t.data) >= 12:
            status, code, size, rid = struct.unpack_from('<4H', t.data, 4)
            controls.append((t, status, code, size, rid))
    requests = [r for r in controls if r[0].is_out]
    acks = [r for r in controls if r[0].is_in]
    matched = sum(any(a[0].frame > r[0].frame and a[0].bus == r[0].bus and a[0].device == r[0].device and a[4] == r[4] and a[2] == r[2]+1 for a in acks) for r in requests)
    images = []
    stream = [t for t in bulk if t.endpoint == 129]
    for i, t in enumerate(stream):
        if t.data[:4] != b'U3VL' or len(t.data) < 52 or i+2 >= len(stream):
            continue
        payload, trailer = stream[i+1:i+3]
        if trailer.data[:4] != b'U3VT' or len(trailer.data) < 28:
            continue
        fid = struct.unpack_from('<Q', t.data, 8)[0]
        ts, pix, width, height = struct.unpack_from('<QIII', t.data, 20)
        tid = struct.unpack_from('<Q', trailer.data, 8)[0]
        declared = struct.unpack_from('<Q', trailer.data, 20)[0]
        images.append({'id': fid, 'trailer_id': tid, 'timestamp_ticks': ts, 'pixel_format': hex(pix), 'width': width, 'height': height, 'declared_bytes': declared, 'captured_bytes': len(payload.data), 'complete': fid == tid and len(payload.data) == declared})
    try:
        guarded_read(path)
        guard = 'accepted'
    except CaptureRejected as e:
        guard = str(e)
    return {'sha256': digest, 'packets': len(packets), 'transfers': len(transfers), 'ids': {str(k): [hex(v) for v in x] for k,x in ids.items()}, 'upstream_sample_assertions': 'PASS', 'bulk_out': len(outs), 'control_requests': len(requests), 'control_responses': len(acks), 'matched': matched, 'control_valid_length': sum(len(t.data) == 12+size for t,_,_,size,_ in controls), 'truncated': truncated, 'images': images, 'guard': guard}

if __name__ == '__main__':
    print(json.dumps(audit(sys.argv[1]), indent=2))
