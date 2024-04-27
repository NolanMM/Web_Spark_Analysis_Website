from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64


class AESCipher:
    def __init__(self, password):
        self.password = password.encode('utf-8')

    def _derive_key(self, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self.password)

    def encrypt(self, plaintext):
        salt = b'\xc2\xae\xa3t\x16\xb1c\xa0\xa5\x82m\x1d\x11\xe2)\xa5'  # Randomly generated salt
        key = self._derive_key(salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(salt), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return base64.urlsafe_b64encode(salt + ciphertext).decode('utf-8')

    def decrypt(self, ciphertext):
        ciphertext = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
        salt = ciphertext[:16]
        ciphertext = ciphertext[16:]
        key = self._derive_key(salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(salt), backend=default_backend())
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
        plaintext = unpadder.update(decrypted_data) + unpadder.finalize()
        return plaintext.decode('utf-8')
