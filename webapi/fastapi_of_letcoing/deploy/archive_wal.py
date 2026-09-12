"""PostgreSQL archive_command 使用的本地/独立挂载归档器，成功前同步文件和目录。"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
from uuid import uuid4


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.digest()


def archive(source, directory):
    source, directory = Path(source), Path(directory)
    if not re.fullmatch(r'[0-9A-F]{24}(?:\.[0-9A-F]{8}\.backup|\.partial)?|[0-9A-F]{8}\.history', source.name):
        raise ValueError('invalid WAL filename')
    if directory.is_symlink() or source.is_symlink():
        raise ValueError('symlinks are not allowed')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = directory/source.name
    temporary = directory/('.pending-'+uuid4().hex)
    try:
        with source.open('rb') as reader, temporary.open('xb') as writer:
            os.chmod(temporary, 0o600)
            shutil.copyfileobj(reader, writer, length=1024*1024)
            writer.flush(); os.fsync(writer.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if destination.is_symlink() or digest(destination) != digest(temporary):
                raise ValueError('WAL archive conflict') from None
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    archive(args.source, args.directory)
