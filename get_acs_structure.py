import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from pprint import pprint

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DESAdapter(HTTPAdapter):
    """
    A custom HTTPAdapter to handle weak SSL ciphers
    """
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        context.check_hostname = False
        kwargs['ssl_context'] = context
        return super(DESAdapter, self).init_poolmanager(*args, **kwargs)

def get_acs_structure(acs_url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Create a session with custom adapter to handle weak SSL
        session = requests.Session()
        session.mount('https://', DESAdapter())
        
        response = session.get(acs_url, headers=headers, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching ACS structure: {e}")
        return f"Error: {str(e)}"

def main():
    acs_url = "https://acs.pub.ro"
    acs_structure = get_acs_structure(acs_url)
    #pprint(acs_structure)
    print(type(acs_structure))

if __name__ == "__main__":
    main()