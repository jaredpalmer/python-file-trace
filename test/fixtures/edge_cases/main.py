# Edge cases test file for Python import tracing

# 1. Multi-line import with backslash continuation
import os, \
    sys, \
    json

# 2. From import with backslash continuation
from collections import \
    OrderedDict, \
    defaultdict

# 3. Multi-line import with parentheses (already partially handled)
from typing import (
    List,
    Dict,
    Optional,
)

# 4. Comma-separated imports
import math, random, time

# 5. Try/except fallback imports
try:
    import fast_module
except ImportError:
    import slow_module

# 6. Conditional imports
import platform
if platform.system() == 'Windows':
    import win_helper
else:
    import unix_helper

# 7. Imports in functions (should still be traced)
def load_extra():
    import extra_module
    return extra_module

# 8. Future imports
from __future__ import annotations

# 9. String that looks like an import (should NOT be traced)
fake_import = "import fake_module"
another_fake = '''
from another_fake import thing
'''

# 10. Comment with import (should NOT be traced)
# import commented_module

# 11. Import after multiline string
multiline = """
This is a
multiline string
"""
import after_multiline

# 12. Aliased importlib
import importlib as il
aliased_dynamic = il.import_module('aliased_target')

# 13. Direct import_module after from import
from importlib import import_module
direct_dynamic = import_module('direct_target')

# 14. import_module with package parameter (relative dynamic import)
relative_dynamic = import_module('.submodule', package='mypackage')

# 15. import_module with keyword arguments
keyword_dynamic = import_module(name='keyword_target')

# 16. Local imports
from mypackage import module_a
from mypackage.module_b import func_b
