import os
import tarfile
import io
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn


class TarFS(LoggingMixIn, Operations):
    def __init__(self, root):
        self.root = root
        self.fd = 0
        self.data = {}
        self.attr = {}
        self.files = [f for f in os.listdir(root) if os.path.isdir(os.path.join(root, f))]
        for file in self.files:
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode='w') as tar:
                tar.add(os.path.join(root, file), arcname='')
            buf.seek(0)
            self.data[file] = buf
            self.attr[file] = dict(st_mode=(0o100644 | 32768), st_nlink=1, st_size=len(buf.getvalue()))

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
        buf = self.data[path[1:]]
        buf.seek(offset)
        return buf.read(size)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    parser.add_argument('mountpoint')
    args = parser.parse_args()
    fuse = FUSE(TarFS(args.root), args.mountpoint, foreground=True)
