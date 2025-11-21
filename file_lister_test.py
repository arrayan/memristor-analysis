from pathlib import Path
import sys

def find_files() -> list:
    ''' POC function, for finding all files in a root folder and storing them in a list

    '''
    src = sys.argv[1]
    print("Root folder:", src)

    files = []
    for path in Path(src).rglob('*.xls'):
        files.append(path)

    print("Filed found:", len(files))

    return files

print(find_files())