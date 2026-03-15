from OpenSSL import SSL
from twisted.internet.ssl import ClientContextFactory

class CustomContextFactory(ClientContextFactory):
    def getContext(self, hostname=None, port=None):
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.set_options(
            SSL.OP_NO_SSLv2 | SSL.OP_NO_SSLv3 |
            SSL.OP_NO_TLSv1 | SSL.OP_NO_TLSv1_1
        )
        ctx.set_cipher_list(b"DEFAULT:@SECLEVEL=1")
        return ctx
