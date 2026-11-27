"""Local durable key custody and sign-once journal; no remote authority claim."""
import os,sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption,PublicFormat
from scientific_consensus import canonical,digest,message
class DurableSigner:
    def __init__(self,home,name):
        self.name=name; home=Path(home); home.mkdir(mode=0o700,parents=True,exist_ok=True)
        if home.stat().st_mode & 0o077:raise ValueError('key directory must be private')
        self.db=sqlite3.connect(home/'signer.db',timeout=10,isolation_level=None)
        os.chmod(home/'signer.db',0o600)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS identity (id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL, key BLOB NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS journal (run TEXT, stage TEXT, hash TEXT NOT NULL, PRIMARY KEY(run,stage))')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.db.execute('SELECT name,key FROM identity WHERE id=1').fetchone()
            if row is None:
                key=Ed25519PrivateKey.generate(); raw=key.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())
                self.db.execute('INSERT INTO identity VALUES(1,?,?)',(name,raw))
            else:
                if row[0]!=name:raise ValueError('identity mismatch')
                key=Ed25519PrivateKey.from_private_bytes(row[1])
            self.db.execute('COMMIT');self.key=key
        except BaseException:self.db.execute('ROLLBACK');raise
    def public(self):return self.key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
    def sign(self,run,stage,body):
        m=message(run,stage,body);h=digest(m);self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.db.execute('SELECT hash FROM journal WHERE run=? AND stage=?',(run,stage)).fetchone()
            if row is not None and row[0]!=h:raise ValueError('conflicting attestation')
            self.db.execute('INSERT OR IGNORE INTO journal VALUES(?,?,?)',(run,stage,h))
            self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
        return {'signer':self.name,'signature':self.key.sign(canonical(m)).hex()}
    def close(self):self.db.close()
