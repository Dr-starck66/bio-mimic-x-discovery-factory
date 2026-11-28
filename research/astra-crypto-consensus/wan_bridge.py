"""Temporary authenticated P2P-only bridge between two research VMs."""
import asyncio, pathlib, sys, os, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from websockets.asyncio.server import serve
from websockets.asyncio.client import connect
root=pathlib.Path('/tmp/astra-wan')
role=sys.argv[1]
domain=b'ASTRA experimental WAN bridge v1\0'
async def pipe(ws,reader,writer):
    async def one():
        while b:=await reader.read(32768):await ws.send(b)
    async def two():
        async for b in ws:
            if not isinstance(b,bytes):raise ValueError("binary only")
            writer.write(b);await writer.drain()
    tasks=[asyncio.create_task(one()),asyncio.create_task(two())]
    try:
        done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
        for t in done:
            try:t.result()
            except Exception:pass
    finally:
        for t in tasks:t.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        writer.close()
        try:await writer.wait_closed()
        except Exception:pass
        await ws.close()
async def main():
    if role=='A':
        meta=json.loads((root/'other/members.json').read_text())
        key=Ed25519PublicKey.from_public_bytes(bytes.fromhex(meta['bridge_pub']))
        active=set()
        async def handler(ws):
            path=ws.request.path
            if path not in [f'/p2p/{i}' for i in range(4)] or (root/'partition.flag').exists():
                await ws.close(1008);return
            active.add(ws)
            try:
                challenge=os.urandom(32);await ws.send(challenge)
                sig=await asyncio.wait_for(ws.recv(),5)
                key.verify(sig,domain+challenge+path.encode())
                if (root/'partition.flag').exists():return
                i=int(path[-1]);r,w=await asyncio.open_connection('127.0.0.1',28000+10*i)
                print('AUTHENTICATED P2P',i,flush=True)
                await pipe(ws,r,w)
            except Exception as e:print('bridge closed',type(e).__name__,flush=True)
            finally:active.discard(ws)
        async def partition():
            while True:
                if (root/'partition.flag').exists() and active:
                    await asyncio.gather(*(w.close(1012) for w in list(active)),return_exceptions=True)
                await asyncio.sleep(.2)
        async with serve(handler,'127.0.0.1',29999,max_size=65536,max_queue=16,ping_interval=10,close_timeout=1):
            print('BRIDGE LISTENING',flush=True)
            await partition()
    else:
        meta=json.loads((root/'other/members.json').read_text());url=meta['tunnel'].replace('https://','wss://',1)
        key=Ed25519PrivateKey.from_private_bytes((root/'bridge.key').read_bytes())
        async def handler(r,w,i):
            path=f'/p2p/{i}'
            try:
                async with connect(url+path,max_size=65536,max_queue=16,open_timeout=15,ping_interval=10,close_timeout=1) as ws:
                    challenge=await asyncio.wait_for(ws.recv(),5)
                    assert isinstance(challenge,bytes) and len(challenge)==32
                    await ws.send(key.sign(domain+challenge+path.encode()))
                    await pipe(ws,r,w)
            except Exception as e:
                print('proxy closed',i,type(e).__name__,flush=True);w.close()
        servers=[await asyncio.start_server(lambda r,w,i=i:handler(r,w,i),'127.0.0.1',29000+i) for i in range(4)]
        print('PROXIES LISTENING',flush=True)
        await asyncio.gather(*(s.serve_forever() for s in servers))
asyncio.run(main())
