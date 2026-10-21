import os
import sys

# Add project root and backend dir to sys.path
root_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(root_dir, ".."))

for p in (root_dir, parent_dir):
    if p not in sys.path:
        sys.path.insert(0, p)
