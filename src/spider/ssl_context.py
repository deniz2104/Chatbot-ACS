from twisted.internet.ssl import CertificateOptions
from twisted.internet._sslverify import ClientTLSOptions
from scrapy.core.downloader.contextfactory import ScrapyClientContextFactory


class CustomContextFactory(ScrapyClientContextFactory):
    def creatorForNetloc(self, hostname, port):
        hostname_str = hostname.decode("ascii") if isinstance(hostname, bytes) else hostname
        ctx = CertificateOptions(verify=False).getContext()
        ctx.set_cipher_list(b"DEFAULT:@SECLEVEL=1")
        return ClientTLSOptions(hostname_str, ctx)
