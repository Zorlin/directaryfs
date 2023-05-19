import os
import time
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn


class DirectaryFS(LoggingMixIn, Operations):
    def __init__(self, root):
        self.root = root
        self.fd = 0
        self.attr = {}
        self.files = [f for f in os.listdir(root) if os.path.isdir(os.path.join(root, f))]
        total_dirs = len(self.files)
        start_time = time.time()
        estimated_sizes = []
        for idx, file in enumerate(self.files):
            print(f"Processing directory: {file}")
            dir_path = os.path.join(root, file)
            if idx < 500:
                dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)))
                estimated_sizes.append(dir_size)
            else:
                dir_size = sum(estimated_sizes) / len(estimated_sizes)
            self.attr[file] = dict(st_mode=(0o100644 | 32768), st_nlink=1, st_size=dir_size)
            elapsed_time = time.time() - start_time
            estimated_time_remaining = (elapsed_time / (idx + 1)) * (total_dirs - idx - 1)
            print(f"Calculated size for directory {idx+1} of {total_dirs}, which is {((idx+1)/total_dirs)*100}%. Size of directory: {dir_size / (1024 * 1024):.2f} MiB. Time elapsed: {elapsed_time:.2f}s. Estimated time to calculate remaining directories: {estimated_time_remaining:.2f}s.")

    def getattr(self, path, fh=None):
        if path == '/':
            return dict(st_mode=(0o755 | 16384), st_nlink=2)
        elif path[1:] not in self.files:
            raise FuseOSError(2)
        return self.attr[path[1:]]

    def readdir(self, path, fh):
        return ['.', '..'] + self.files

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        dir_path = os.path.join(self.root, path[1:])
        dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)))
        return str(dir_size).encode()[offset:offset + size]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    parser.add_argument('mountpoint')
    args = parser.parse_args()
    fuse = FUSE(DirectaryFS(args.root), args.mountpoint, foreground=True)
