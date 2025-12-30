# Test file for runpy edge cases

# 1. Standard runpy.run_module usage
import runpy
result1 = runpy.run_module('target_module')

# 2. Aliased runpy import
import runpy as rp
result2 = rp.run_module('aliased_target')

# 3. runpy.run_path usage
result3 = runpy.run_path('scripts/runner.py')

# 4. Dynamic module name (should warn, not trace)
module_name = "dynamic_module"
result4 = runpy.run_module(module_name)

# 5. run_module with keyword argument
result5 = runpy.run_module(mod_name='keyword_module')
