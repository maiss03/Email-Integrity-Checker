
from Crypto.PublicKey import RSA

def generate_keys():
    key = RSA.generate(2048)
    private_key = key
    public_key = key.publickey()

   
    with open("private.pem", "wb") as f:
        f.write(private_key.export_key())
    with open("public.pem", "wb") as f:
        f.write(public_key.export_key())

generate_keys()
