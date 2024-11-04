import sys
import subprocess

subprocess.run(
    [
        sys.executable,
        'setup.py',
        'install'
    ]
)
