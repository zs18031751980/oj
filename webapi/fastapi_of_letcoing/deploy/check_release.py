"""在迁移/Worker 启动前验证发布镜像不可变引用，不访问外部服务。"""
import argparse
import os
import re


def validate_images(role):
    if role not in {'api', 'worker'}:
        raise ValueError('invalid deployment role')
    keys = ['API_IMAGE' if role == 'api' else 'WORKER_IMAGE', 'JUDGE_SANDBOX_IMAGE']
    for key in keys:
        if not re.fullmatch(r'(?:[a-zA-Z0-9][a-zA-Z0-9._:/-]*@)?sha256:[0-9a-f]{64}', os.environ.get(key, '')):
            raise ValueError(f'{key} must use an immutable sha256 image reference')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=['api', 'worker'], required=True)
    args = parser.parse_args()
    validate_images(args.role)
