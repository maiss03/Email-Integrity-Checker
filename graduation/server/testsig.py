from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import base64

# تحميل المفتاح الخاص
private_key = RSA.import_key(open('private.pem').read())

# الرسالة لتوقيعها
message = "This is a secret message"
hash = SHA256.new(message.encode())

# توقيع الرسالة باستخدام المفتاح الخاص
signer = pkcs1_15.new(private_key)
signature = signer.sign(hash)

# حفظ التوقيع في ملف لسهولة الاختبار (اختياري)
with open("signature.sig", "wb") as sig_file:
    sig_file.write(signature)

# تحميل المفتاح العام للتحقق من التوقيع
public_key = RSA.import_key(open('public.pem').read())

# التحقق من التوقيع
verifier = pkcs1_15.new(public_key)
try:
    verifier.verify(hash, signature)
    print("The signature is valid.")
except (ValueError, TypeError):
    print("The signature is invalid.")
