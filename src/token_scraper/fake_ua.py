#"chrome": ["windows", "macos","linux"],
#"firefox": ["windows", "macos","linux"],
# "edge" : ["windows", "macos","linux"],
#"safari": ["macos"],

import ua_generator
from ua_generator.data.version import VersionRange
from ua_generator.options import Options

options = Options()
options.version_ranges = {'chrome': VersionRange(min_version=145, max_version=145)}

ua = ua_generator.generate(browser='chrome', options=options)
print(ua)