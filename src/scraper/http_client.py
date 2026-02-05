import requests
from urllib3.util.ssl_ import create_urllib3_context
import urllib3

urllib3.disable_warnings()
class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        context.check_hostname = False
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)
