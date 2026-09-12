"""在专用判题节点采样 CPU 用时；与同镜像的其他节点比较，不修改主机调频设置。"""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.compile_cache import prepare_cached

SOURCE = '''#include <iostream>
int main(){volatile unsigned long long n=0; for(unsigned long long i=0;i<20000000;i++) n=n+i; std::cout<<n;}'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=10)
    parser.add_argument('--max-cv', type=float, default=.2)
    parser.add_argument('--output', type=Path, default=Path('judge-calibration.json'))
    args = parser.parse_args()
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
