/** 资源树的排序工具：文件夹优先 + 文件名自然（数值）排序 */

/** 自然排序比较：把连续数字当作数值比较，其余按中文本地化比较 */
export function naturalCompare(a: string, b: string): number {
  const re = /(\d+)|(\D+)/g;
  const ax: Array<string | number> = [];
  const bx: Array<string | number> = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(a)) !== null) ax.push(m[1] !== undefined ? parseInt(m[1], 10) : m[2] as string);
  while ((m = re.exec(b)) !== null) bx.push(m[1] !== undefined ? parseInt(m[1], 10) : m[2] as string);
  const len = Math.max(ax.length, bx.length);
  for (let i = 0; i < len; i++) {
    const av = ax[i];
    const bv = bx[i];
    if (av === undefined) return -1;
    if (bv === undefined) return 1;
    if (typeof av === 'number' && typeof bv === 'number') {
      if (av !== bv) return av - bv;
    } else if (typeof av === 'string' && typeof bv === 'string') {
      const c = av.localeCompare(bv, 'zh-CN');
      if (c !== 0) return c;
    } else {
      return typeof av === 'number' ? -1 : 1;
    }
  }
  return 0;
}

/** 文件夹优先，同级按 path 做自然（数值）排序 */
export function sortNodesFoldersFirst<T extends { type: string; path: string }>(nodes: T[]): T[] {
  return [...nodes].sort((a, b) => {
    if (a.type === 'folder' && b.type !== 'folder') return -1;
    if (a.type !== 'folder' && b.type === 'folder') return 1;
    return naturalCompare(a.path, b.path);
  });
}
