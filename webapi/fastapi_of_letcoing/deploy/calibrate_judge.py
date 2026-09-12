"""在专用判题节点采样 CPU 用时；与同镜像的其他节点比较，不修改主机调频设置。"""
import argparse
import json
import os
import re
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.compile_cache import prepare_cached

SOURCE = '''#include <iostream>
int main(){volatile unsigned long long n=0; for(unsigned long long i=0;i<20000000;i++) n=n+i; std::cout<<n;}'''


def compare_calibrations(reports, max_ratio=1.1, max_cv=.2):
    import math
    if len(reports) < 2 or not 1 <= max_ratio <= 2 or not 0 < max_cv < 1:
        raise ValueError('至少两个节点报告，阈值必须有效')
    medians, images = [], set()
    for report in reports:
        if not isinstance(report, dict):
            raise ValueError('节点报告必须为对象')
        image = report.get('image')
        if not isinstance(image, str) or not re.fullmatch(
                r'(?:[a-zA-Z0-9][a-zA-Z0-9._:/-]*@)?sha256:[0-9a-f]{64}', image):
            raise ValueError('节点报告必须使用不可变镜像摘要')
        values = report.get('cpu_ms', [])
        if not isinstance(values, list) or not 5 <= len(values) <= 100 or any(type(v) not in (float, int) or not math.isfinite(v) or v <= 0 for v in values):
            raise ValueError('节点报告必须包含至少五个正 CPU 时间样本')
        images.add(report.get('image'))
        if statistics.pstdev(values)/statistics.mean(values) > max_cv:
            return {'passed': False, 'reason': 'unstable_node'}
        medians.append(statistics.median(values))
    ratio = max(medians)/min(medians)
    return {'passed': len(images) == 1 and None not in images and ratio <= max_ratio,
            'node_count': len(reports), 'median_ratio': ratio, 'same_image': len(images) == 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=10)
    parser.add_argument('--max-cv', type=float, default=.2)
    parser.add_argument('--output', type=Path, default=Path('judge-calibration.json'))
    parser.add_argument('--compare', type=Path, nargs='+', help='比较已有节点报告，不执行程序')
    parser.add_argument('--max-ratio', type=float, default=1.1)
    args = parser.parse_args()
    if args.compare:
        result = compare_calibrations([json.loads(path.read_text()) for path in args.compare], args.max_ratio, args.max_cv)
        args.output.write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        return 0 if result['passed'] else 1
    if not 5 <= args.samples <= 100 or not 0 < args.max_cv < 1:
        parser.error('样本数或变异系数阈值无效')
    if os.environ.get('JUDGE_BACKEND', 'docker') != 'docker' or os.environ.get('APP_ENV') != 'production':
        parser.error('校准必须使用生产 Docker 隔离配置')
    program, error, _ = prepare_cached(SOURCE, 'cpp')
    if error or program is None:
        raise RuntimeError('校准程序编译失败')
    values = []
    try:
        for index in range(args.samples+1):
            output, error, _, _ = program.run('', 3, 128)
            if error or output.strip() != '199999990000000':
                raise RuntimeError('校准程序执行失败')
            if index:
                values.append(program.last_metrics['cpu_time'])
    finally:
        program.close()
    mean = statistics.mean(values)
    cv = statistics.pstdev(values)/mean if mean else float('inf')
    result = {'image': os.environ.get('JUDGE_SANDBOX_IMAGE'), 'cpuset': os.environ.get('JUDGE_CPUSET'),
        'cpu_ms': values, 'median_cpu_ms': statistics.median(values),
        'coefficient_of_variation': cv if mean else None, 'passed': bool(mean) and cv <= args.max_cv}
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
