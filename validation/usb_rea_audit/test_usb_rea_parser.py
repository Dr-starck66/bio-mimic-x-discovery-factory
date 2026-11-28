import struct, tempfile, unittest
from pathlib import Path
from usb_rea.pcap import read_transfers, find_ids
from usb_rea.model import Transfer

# Independent synthetic fixtures, no physical USB commands.
def usbmon(payload, bus=1, dev=7, ep=1, event=b'S', xtype=3, setup=b'\0'*8, has_setup=False, declared=None):
    n=len(payload) if declared is None else declared
    return struct.pack('<QcBBBHccqiiII8s', 1,event,xtype,ep,dev,bus,b'\0' if has_setup else b'-',b'\0',0,0,0,n,n,setup)+payload

def usbpcap(payload, ep=1, completion=0, bus=1, dev=7):
    return struct.pack('<HQIHBHHBBI',27,1,0,0,completion,bus,dev,ep,3,len(payload))+payload

def pcap(lt, packets):
    return struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,lt)+b''.join(struct.pack('<IIII',10,i,len(p),len(p))+p for i,p in enumerate(packets))

def pcapng(lt, packets):
    def block(t,b):
        b=b+b'\0'*((-len(b))%4); n=len(b)+12
        return struct.pack('<II',t,n)+b+struct.pack('<I',n)
    return block(0x0a0d0d0a,struct.pack('<IHHq',0x1a2b3c4d,1,0,-1))+block(1,struct.pack('<HHI',lt,0,65535))+b''.join(block(6,struct.pack('<IIIII',0,0,i+1,len(p),len(p))+p) for i,p in enumerate(packets))

def parse(blob):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'fixture';p.write_bytes(blob);return read_transfers(p)

class ParserTests(unittest.TestCase):
    def test_linux_out_in(self):
        t=parse(pcap(189,[usbmon(b'abc'),usbmon(b'def',ep=0x81,event=b'C')]))
        self.assertEqual([(x.endpoint,x.data) for x in t],[(1,b'abc'),(129,b'def')])
    def test_linux_mmapped(self):
        p=usbmon(b'abc');t=parse(pcap(220,[p[:48]+b'\0'*16+p[48:]]));self.assertEqual(t[0].data,b'abc')
    def test_windows_pcapng(self):
        t=parse(pcapng(249,[usbpcap(b'abc'),usbpcap(b'def',ep=129,completion=1)]));self.assertEqual([x.data for x in t],[b'abc',b'def'])
    def test_invalid_magic(self):
        with self.assertRaises(ValueError):parse(b'not a capture')
    def test_empty_capture(self):
        self.assertEqual(parse(pcap(189,[])),[])
    def test_duplicate_completion_ignored(self):
        self.assertEqual(len(parse(pcap(189,[usbmon(b'abc'),usbmon(b'abc',event=b'C')]))),1)
    def test_identity_across_buses(self):
        a,b=parse(pcap(189,[usbmon(b'a',bus=1),usbmon(b'b',bus=2)]));self.assertNotEqual(a.key(),b.key())
    def test_truncated_payload_rejected(self):
        t=parse(pcap(189,[usbmon(b'a',declared=5)]));self.assertEqual(t,[])
    def test_descriptor_across_buses(self):
        setup=bytes.fromhex('8006000100001200');desc=bytes.fromhex('120100020000004034127856000000000001')
        t=parse(pcap(189,[usbmon(b'',bus=1,ep=0,xtype=2,setup=setup,has_setup=True),usbmon(desc,bus=2,ep=128,event=b'C',xtype=2)]))
        self.assertEqual(find_ids(t),{})

if __name__=='__main__':unittest.main(verbosity=2)
