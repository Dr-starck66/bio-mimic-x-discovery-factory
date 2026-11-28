import tempfile,unittest
from pathlib import Path
from test_usb_rea_parser import pcap,pcapng,usbmon,usbpcap
from astra_usb_guard import guarded_read,guarded_ids,CaptureRejected

def run(blob, fn=guarded_read):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'fixture';p.write_bytes(blob);return fn(p)

class GuardTests(unittest.TestCase):
    def test_linux_normal(self): self.assertEqual(run(pcap(189,[usbmon(b'abc')]))[0].data,b'abc')
    def test_windows_normal(self): self.assertEqual(run(pcapng(249,[usbpcap(b'abc')]))[0].data,b'abc')
    def test_mixed_buses(self):
        with self.assertRaises(CaptureRejected):run(pcap(189,[usbmon(b'a',bus=1),usbmon(b'b',bus=2)]))
    def test_truncated(self):
        with self.assertRaises(CaptureRejected):run(pcap(189,[usbmon(b'a',declared=5)]))
    def test_mixed_descriptor(self):
        setup=bytes.fromhex('8006000100001200');desc=bytes.fromhex('120100020000004034127856000000000001')
        with self.assertRaises(CaptureRejected):run(pcap(189,[usbmon(b'',bus=1,ep=0,xtype=2,setup=setup,has_setup=True),usbmon(desc,bus=2,ep=128,event=b'C',xtype=2)]),guarded_ids)
    def test_windows_mixed_buses(self):
        with self.assertRaises(CaptureRejected):run(pcapng(249,[usbpcap(b'a',bus=1),usbpcap(b'b',bus=2)]))
    def test_windows_truncated(self):
        with self.assertRaises(CaptureRejected):run(pcapng(249,[usbpcap(b'abc')[:-1]]))
    def test_mmapped(self):
        p=usbmon(b'abc');self.assertEqual(run(pcap(220,[p[:48]+b'\0'*16+p[48:]]))[0].data,b'abc')

if __name__=='__main__':unittest.main(verbosity=2)
