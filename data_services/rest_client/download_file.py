"""
Code for downloading an input file via the REST API.

This module can be called as a stand-alone script from a shell script (*nix) or command script (Windows).
Or the module can be imported, and its download_file function called from Python code.
"""

import requests
import sys


def main():
    if len(sys.argv) != 3:
        print "Usage: %s url filename" % sys.argv[0]
        sys.exit(1)
    url = sys.argv[1]
    filename = sys.argv[2]
    print "Downloading..."
    download_file(url, filename)
    print "done"


def download_file(url, local_filename):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'w+') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()

if __name__ == '__main__':
    main()
