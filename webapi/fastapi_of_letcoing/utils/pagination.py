"""显式分页保持旧客户端兼容，拒绝无界页尺寸与异常偏移。"""
def pagination(args):
    if 'page' not in args and 'page_size' not in args:
        return None
    try:
        page = int(args.get('page', '1'))
        size = int(args.get('page_size', '50'))
    except (ValueError, TypeError):
        raise ValueError('page 和 page_size 必须是整数') from None
    if not 1 <= page <= 10000 or not 1 <= size <= 100:
        raise ValueError('page 范围为 1–10000，page_size 范围为 1–100')
    return (page-1)*size, size
