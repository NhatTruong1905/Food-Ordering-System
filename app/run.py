import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app, index

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
