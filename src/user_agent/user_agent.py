import ua_generator

from ua_generator.data.version import VersionRange
from ua_generator.options import Options
from src.user_agent.browser_versions import Browser

def _set_options_for_browsers() -> Options:
    options = Options()
    options.weighted_versions = True
    options.version_ranges = {
        b.browser_name: VersionRange(min_version=b.min_version)
        for b in Browser
    }
    return options

def create_browser_header() -> ua_generator.Header:
    options = _set_options_for_browsers()
    browsers = set(b.browser_name for b in Browser)
    return ua_generator.generate(device="desktop", browser=browsers, options=options)