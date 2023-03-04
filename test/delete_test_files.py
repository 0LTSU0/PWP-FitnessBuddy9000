"""
Workaround method for permission error in actual testing files
"""
import os

files = [f for f in os.listdir('.') if os.path.isfile(f)]

for item in files:
    if item.startswith("temppytest_"):
        os.remove(item)
