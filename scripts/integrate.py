#!/usr/bin/env python3
"""Historical one-time release automation; retained releases contain the original implementation."""
import sys
print("This one-time archival command is retired. Use REPRODUCE.md for verification and docs/INTEGRATION.md for maintenance. Original automation is preserved at tag v0.2.0.")
if len(sys.argv)>1 and sys.argv[1] not in ('--help','-h'):
    raise SystemExit(2)
