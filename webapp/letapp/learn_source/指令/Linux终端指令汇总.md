# Linux 终端指令详解大全（含缩写来源、参数表、实战示例）

> 适用于 Debian / Ubuntu 系（`sudo apt`）与通用 Linux。
> 每个命令包含三类信息：
> - **`命令`** —— 一条或整串（`反引号` 表示输入）
> - **`缩写来源`** —— 命令命名由来，帮助记忆
> - **举一反三的实战示例** —— 结合真实场景
>
> 约定：`[可选]` 方括号；`<必填>` 尖括号；`<服务器名>|<备选>` 竖线表示选择。

---

## 目录
1. [文件与目录](#1-文件与目录)
2. [查看与搜索](#2-查看与搜索)
3. [文本处理与正则](#3-文本处理与正则)
4. [权限与用户](#4-权限与用户)
5. [进程与系统监控](#5-进程与系统监控)
6. [网络与远程](#6-网络与远程)
7. [软件安装（apt / dpkg）](#7-软件安装apt--dpkg)
8. [磁盘存储与挂载](#8-磁盘存储与挂载)
9. [压缩与归档](#9-压缩与归档)
10. [Git 版本控制](#10-git-版本控制)
11. [Shell 脚本基础](#11-shell-脚本基础)
12. [日常工作流（组合实战）](#12-日常工作流组合实战)
13. [常用快捷键](#13-常用快捷键)
14. [命令命名规律与记忆技巧](#14-命令命名规律与记忆技巧)

---

## 1. 文件与目录

### 1.1 最基本的三连：`pwd` / `ls` / `cd`
```bash
pwd        # Print Working Directory —— 打印当前工作目录（再按下方向键↑可复用）
ls         # List —— 列出当前目录内容
cd <目录>  # Change Directory —— 切换目录
```

**`ls` 常用参数表**
| 参数 | 作用 | 来源 |
|------|------|------|
| `-l` | 长格式（权限、属主、大小、时间） | long 长 |
| `-a` | 显示隐藏文件（以 `.` 开头） | all 全部 |
| `-h` | 人类可读大小（K/M/G） | human 人类 |
| `-t` | 按修改时间排序 | time 时间 |
| `-S` | 按文件大小排序 | Size |
| `-r` | 反向排序 | reverse 反向 |
| `-R` | 递归显示子目录 | Recursive |
| `-d` | 只显示目录本身 | directory |
| `-i` | 显示 inode 号 | inode |

**`ls -l` 输出图解：**
```
-rw-r--r-- 1 z    z    2341  8月 5日  07:14  main.cpp
└─┬───┬─┘ │ └┬─┘ │   └┬┘    └┬────┘  └──┬───┘
  │   │   │  │   │    │       │          └ 文件名
  │   │   │  │   │    │       └ 修改时间
  │   │   │  │   │    └ 文件大小（字节）
  │   │   │  │   └ 所属组 group
  │   │   │  └ 属主 owner（拥有者）
  │   │   └ 硬链接数 / 目录项数
  │   └ 属主 权限 rwx | 组 r-x | 其他 r--
  └ 文件类型：-文件  d目录  l链接  c字符设备  b块设备
```

**`cd` 高频写法**
```bash
cd .          # 当前目录（. 表示这里）
cd ..         # 上级目录（.. 上级）
cd ../..      # 上两级
cd ~          # 家目录（~ 波浪号 = $HOME）
cd -          # 返回上一次所在目录（很实用）
cd /          # 根目录
cd ~/文档/Default Project   # 路径含空格时用引号：cd "~/文档/Default Project"
```

### 1.2 创建与管理
```bash
mkdir <目录>        # MaKe DIRectory 创建目录
mkdir -p a/b/c      # -p parents 递归创建多级（没有就先建）
mkdir -m 755 d      # -m mode 指定权限创建

touch <文件>        # 创建空文件；已存在则只更新时间戳
truncate -s 100M a  # 快速生成指定大小文件（测试用）
cp    <源> <目标>   # CoPy 复制
cp -r <源目录> <目录2>  # 递归复制整目录
cp -i 源 目标       # 覆盖前询问（更安全）
cp -a 源 目标       # 递归复制并保留属性（备份常用，archive）
mv  <源> <目标>     # MoVe 移动或重命名（改名 = 移动到新名字）
mv 老名 新名        # 纯重命名示例
rm <文件>           # ReMove 删除
rm -r <目录>        # 递归删目录
rm -rf <目录>       # 强制递归删除（f=force），**高危**
rm -i 文件          # 删除前逐个询问

ln -s /真实/目标 /链接/名  # LiNk 建立软链接（类似 Windows 快捷方式）
ls -l               # 软链接显示为 xxx -> 目标
rm /链接/名         # 删除链接本身（不影响目标）
```

### 1.3 查找文件 `find`
```bash
find <起点目录> <条件> <动作>
find /home -name "*.png"          # 按名称（-name，区分大小写）
find /home -iname "*.PNG"         # -i 忽略大小写
find /    -type f                 # 只看文件 f / 目录 d
find /var -type d -name "log*"    # 组合条件
find /    -size +100M             # 大于 100M 的文件
find /    -mtime -7               # 7 天内修改过的（-7 以内，+7 以前）
find /    -user z                 # 属于用户 z 的文件
find /    -perm 644               # 权限恰好 644 的
find / -name "*.tmp" -delete      # 找到并删除
find / -name "*.log" -exec rm {} \;  # 找到并对每个执行命令
```
> `locate`（更快但依赖数据库）：先 `sudo updatedb` 建库，再 `locate 关键词`。

---

## 2. 查看与搜索

```bash
cat <文件>     # conCATenate 串联输出全部内容
cat a b        # 可一次查看多个文件
head -20 f     # 看开头 20 行（默认 10 行）
tail -20 f     # 看结尾 20 行
tail -f f      # -f follow 实时跟踪，监控日志神器（Ctrl+C 退出）
less <文件>    # 分页浏览（more 的增强版，可上翻）
#   less 内操作：↑↓ 翻行  /关键词 搜索  n下一个  q退出  g首行 G尾行
more <文件>    # 老式分页（只能向下）
nl <文件>      # Number Lines 带行号查看
stat <文件>    # 查看文件详细属性（权限、时间、inode）
file <文件>    # 判断文件类型（识别二进制/文本）
which <命令>   # 查找命令所在路径，如 which python3
type <命令>    # 判断：内置命令 or 外部命令
```

### grep 搜索
```bash
grep "error" /var/log/syslog        # 查找包含 error 的行
grep -i "error" 日志                # -i ignore 忽略大小写
grep -n "error" 日志                # -n 显示行号
grep -r "TODO" /home/xxx/项目目录   # -r 目录递归
grep -v "日志"                      # -v invert 反向（不匹配的）
grep -c "error" 日志                # -c count 统计次数
grep -w "word"                      # -w 精确匹配整个单词（不匹配 wordpress）
grep -E "2024|2025" 日志            # -E 扩展正则，等于 egrep，| 表示"或"
grep -l "error" /var/log/*          # -l 只列文件名
grep -H "error" 文件                # -H 显示文件名
command | grep "关键词"             # 最常用：管道，筛选命令输出
```
> **管道组合**：`ps aux | grep python` = 找出所有 python 进程。这是最实用的一招。

---

## 3. 文本处理与正则

```bash
echo "hello"             # 打印文本（echo 回声）
echo "v: $HOME"          # 变量展开（$ 取值） 
echo "v: \$HOME"         # 加 \ 转义后原样输出 $HOME

sort 名单.txt            # 排序（默认按字母）
sort -n 数字.txt         # 按数值排序（number）
sort -r 名单.txt         # 反向排序
sort 文件 | uniq         # 去重（必须先排序）
uniq -c 文件             # 统计每项出现次数（-c count）

wc 文件                  # Word Count：行数 单词数 字节数
wc -l 文件               # 只统计行数（最常用）
wc -w 文件               # 单词数
wc -c 文件               # 字节数（中文按 UTF-8 每字占 3 字节左右）

cut -d: -f1 /etc/passwd  # CUT：-d 分隔符 -f 字段，取第一段
echo "a:b:c" | cut -d: -f2    # 输出 b
head -5 f | cut -c1-10   # -c 按字符位置截取，取每行前10字符

tr 'a-z' 'A-Z' < 文件    # TRanslate 大小写转换
tr -d '空格' < 文件       # -d delete 删除字符
tr -s ' ' < 文件          # -s squeeze 压缩连续重复为1个

diff a b                 # DIFFerence 逐行比较差异
diff -u a b              # 统一格式（patch 用）
cmp a b                  # 只告诉你是否相同
```

### 正则表达式速查（供 grep -E / sed / vim 使用）
| 元字符 | 含义 | 示例 |
|--------|------|------|
| `^` | 行首 | `^error` 以 error 开头 |
| `$` | 行尾 | `error$` 以 error 结尾 |
| `.` | 任意单字符 | `h.t` → hat/hot/hut |
| `*` | 前一个字符重复多次 | `ab*c` → ac/abc/abbbc |
| `+` | 前一个至少一次（E模式） | `ab+c` → abc/abbbc |
| `?` | 前一个 0 或 1 次 | `colou?r` → color/colour |
| `[abc]` | 其中一个字符 | `[0-9]` 任意数字 |
| `[^abc]` | 非括号内字符 | `[^0-9]` 非数字 |
| `a\|b` | 或（E模式） | `cat\|dog` |
| `\{n\}` | 恰好 n 次 | `[0-9]\{3\}` 三位数 |
| `\(\)` | 分组 | `\(ab\)+` ab 重复多次 |

---

## 4. 权限与用户

```bash
whoami            # WHO AM I 我是谁（当前用户）
id                # IDentity 显示 uid/gid/组
id -u             # 只看 uid
sudo <命令>       # Super User DO 以 root 执行  <- 前缀，重要！

chmod 权限 文件    # CHange MODe 修改权限
chmod +x 脚本.sh  # 加执行权限（运行脚本必需）
chmod -x 文件      # 去掉执行权限
chmod u+x 文件    # u=属主 g=属组 o=其他 a=全部
chmod 664 文件    # 数字方式（见下表）
chmod -R 755 目录  # -R 递归应用到子目录
chown 用户:组 文件  # CHange OWNer 改属主属组
chown z:z 文件
chgrp 组 文件       # CHange GRouP 只改属组
```

**权限数字计算（rwx 每位 1 或 0）**
```
权限   r w x   二进制   数字
---↑
rwx =  1 1 1  → 4+2+1 = 7   读+写+执行
rw- =  1 1 0  → 4+2+0 = 6   读+写
r-x =  1 0 1  → 4+0+1 = 5   读+执行
r-- =  1 0 0  → 4+0+0 = 4   只读
-w- =  0 1 0  → 0+2+0 = 2   只写
chmod 755 = 属主7(rwx) 属组5(rx) 其他5(rx)   ← 最常用，普通程序文件
chmod 644 = 属主6(rw)  属组4(r)  其他4(r)    ← 普通文件默认
chmod 600 = 属主6(rw)  其他无             ← 私密文件，如密钥
chmod 777 = 全部可读写执行           ← **危险**，少用
```

**用户管理**
```bash
sudo adduser 新用户        # 交互式创建用户（创建家目录）
sudo userdel 新用户        # USER DELete 删除用户
sudo userdel -r 新用户     # -r 连同家目录一起删
sudo usermod -aG sudo 用户 # 把用户加入 sudo 组（给管理员权限）
sudo passwd 用户名          # 设置用户密码
passwd                     # 改自己密码
who / last / lastlog       # 登录情况排查
sudo chage -l 用户          # 查看密码过期策略
```

---

## 5. 进程与系统监控

```bash
# —— 进程查看 ——
ps                        # Process Status 当前终端进程快照
ps aux                    # 全部进程（a all / u user / x 含无终端）
ps -ef                    # 更完整列表（-f 全格式）
ps aux | grep python      # 找特定程序进程 ← 最常用
pidof 程序名              # 直接拿 PID（PID 是进程号 Process ID）
pgrep -l 程序名           # 按名字找进程并显示 PID

top                       # Table Of Processes 实时刷新（q 退出）
htop                      # 增强版（彩色，需安装 sudo apt install htop）
  # top 内：M 按内存排  P 按CPU排  1 看每核  k 杀进程

kill <PID>                # 发 KILL 信号终止进程
kill -9 <PID>             # 强制杀死（SIGKILL，无法忽略）
kill -15 <PID>            # 礼貌终止（SIGTERM，默认）
pkill 程序名              # 按名字终止
killall 程序名            # 终止全部同名进程

# —— 后台任务 ——
命令 &                    # 后台运行（马上回到提示符）
nohup 命令 &              # No Hang UP 不挂断运行（关闭终端也不死，日志存 nohup.out）
jobs                      # 查看后台任务
fg                        # ForeGround 调到前台
bg                        # BackGround 调到后台
Ctrl+C                    # 前台强行中断
Ctrl+Z                    # 挂起，然后用 bg 转后台

# —— 系统硬件 ——
uname -a                  # UNIX Name，内核与系统信息
uname -r                  # 只显示内核版本
hostnamectl               # 主机名+系统发行版
free -h                   # FREE 内存（-h 人类可读）
lscpu                     # 查看 CPU 信息
lsusb                     # 查看 USB 设备
lspci                     # 查看 PCI 设备（显卡/网卡等）
uptime                    # 开机时长 + 平均负载
w                         # 当前登录用户和负载
date                      # 日期时间
cal                       # 日历
```

---

## 6. 网络与远程

```bash
# —— 本机网络状态 ——
ip a                     # IP 地址（a=address）
ip link                  # 网卡开关状态
ip route 或 ip r          # 路由/默认网关
hostname                 # 主机名
hostname -I              # 本机所有 IP
ss -tulpn                # Socket Statistics 端口监听（现代，推荐）
netstat -tulpn           # 旧式端口监听
  # 参数：-t tcp -u udp -l listen监听 -p process进程 -n 数字不解析
sudo ss -tulpn | grep :22 # 查某端口

# —— 网络测试 ——
ping <主机/IP>           # 测连通性与延迟（Ctrl+C 停止）
ping -c 4 <主机>         # 只看 4 次
curl <URL>               # Client URL 发送请求/下载
curl -I <URL>            # 只看响应头
curl -o 文件 <URL>       # 下载保存到指定文件
wget <URL>               # 下载文件
wget -c <URL>            # 断点续传（continue）

# —— 远程接管 ——
ssh <用户>@<主机>        # Secure SHell 远程登录
ssh -p 2222 用户@主机    # 指定端口
scp 文件 用户@主机:/路径  # Secure CoPy 本地上传
scp 用户@主机:/路径 文件   # 远程下载到本地
scp -r 目录 用户@主机:/路径 # -r 传目录
sftp <用户>@<主机>       # 交互式 secure 文件传输，类 ftp

# —— DNS 解析 ——
nslookup <域名>          # Name Server LookUP 基本解析
dig <域名>               # Domain Information Groper 详细解析
host <域名>              # 简单解析
```
> **快捷键**：按 `Ctrl+Z` 挂起 ssh、回到本机，`fg` 再回 ssh，避免长连接断。

---

## 7. 软件安装（apt / dpkg）

```bash
# APT 全套流程（日常最常用）
sudo apt update             # 更新软件源索引（第一步，必做）
sudo apt upgrade            # 升级所有已装软件
sudo apt install <包>       # 安装
sudo apt install <包1> <包2> # 一次装多个
sudo apt remove <包>        # 卸载（保留配置文件）
sudo apt purge <包>         # 卸载（连配置一起删）
sudo apt autoremove         # 清理自动安装但已无用的依赖
sudo apt clean              # 清空下载的缓存
sudo apt full-upgrade       # 完整升级（允许增删包）

# 搜索与信息
apt search <关键词>          # 搜索软件
apt show <包>               # 查看包详情
apt list --installed        # 列出已安装
apt-cache depends <包>      # 看依赖关系

# dpkg 手动管理（APT 底层）
sudo dpkg -i 包.deb         # Debian Package 安装本地 .deb 文件
sudo dpkg -r <包名>         # 卸载
dpkg -l                     # 列出所有已装包
dpkg -l | grep 关键词        # 查某个包装没装
dpkg -S /路径/文件           # 查文件属于哪个包
```

**为什么有时 `sudo apt install 版本不够新`？**
> Debian 官方源比较保守（稳定优先）。需要新版本时要加第三方源或源码编译，
> 例如本项目里的 `OpenXLSX`（源码 cmake 编译安装）、`Arrow/Parquet`（pkg-config 链接）。

**用 apt 安装本项目已常用的库（对应 main.cpp）**
```bash
sudo apt install libeigen3-dev             # Eigen 矩阵库
sudo apt install libboost-all-dev          # Boost / Boost.Math / Asio
sudo apt install libgsl-dev                # GSL 科学计算
sudo apt install libarmadillo-dev libopenblas-dev  # Armadillo+OpenBLAS
sudo apt install libvtk9-dev               # VTK 可视化（含 OpenGL）

CXX 编译链接参考（当前项目属于"多库组合"，用 CMake + pkg-config 管理更稳）
```

---

## 8. 磁盘存储与挂载

```bash
df -h                 # Disk Free 各分区剩余空间（-h 人类可读）
df -h / 或 df -h /home # 只看某分区
du -sh 目录            # Disk Usage 统计目录占用（-s sum 汇总）
du -sh *              # 查看当前目录每个子目录大小
lsblk                 # LiSt BLocK 列出所有块设备分区树
blkid                 # Block ID 查设备 UUID/类型/标签
sudo fdisk -l         # 显示磁盘分区详情
sudo fdisk <设备>      # 进入分区交互工具（危险）
sudo mkfs.ext4 <设备>  # MaKe FileSystem 格式化（**会清空数据**）
mount <设备> <挂载点>  # 挂载
umount <挂载点>        # 卸载
sudo mount /dev/sdb1 /mnt/data
sudo fsck <设备>       # File System ChecK 检查修复
swapon / swapoff       # 开关交换分区
```

**分区命名速记**：`/dev/sdX1`（X=线序，数字=分区号）；NVMe 则是 `/dev/nvme0n1p1`。

---

## 9. 压缩与归档

### tar（Tape ARchive——磁带归档，最初用于磁带）
| 常用写法 | 说明 |
|----------|------|
| `tar -czvf 包.tar.gz 目录` | **打包+gzip 压缩**（最常用） |
| `tar -xzvf 包.tar.gz` | 解压到当前目录 |
| `tar -tzvf 包.tar.gz` | 只列出内容不解压（t=list） |
| `tar -cjvf 包.tar.bz2 目录` | bzip2 压缩（更小但更慢） |
| `tar -cJvf 包.tar.xz 目录` | xz 压缩（更小更慢） |
| `tar -czvf 包.tar.gz -C /路径 .` | 指定解包根目录 |

**tar 选项字母记忆口诀**：
```
c 创建(create)
x 解压(extract)
z gzip压缩
j bzip2压缩
J xz压缩
v 显示过程(verbose)
f 后面是文件名(file，必须放最后)
t 列出内容(test/list)
```

```bash
tar -czf backup.tar.gz myproject   # 打包 myproject 成 .tar.gz
tar -xzf backup.tar.gz             # 解压
tar -xzf backup.tar.gz -C /目标目录/ # 解压到指定目录
```

### zip / gzip / bzip2
```bash
zip -r 包.zip 目录      # 压缩成 zip（-r 递归含子目录）
unzip 包.zip            # 解压 zip
unzip 包.zip -d /目录/   # 解压到指定目录
zip -e 包.zip 文件       # -e encrypt 加密码保护

gzip 文件               # 文件变 文件.gz（自动删原文）
gunzip 文件.gz           # 还原
bzip2 文件 / bunzip2 文件.bz2
```
> Windows/zip、Mac/zip、Linux/tar 之间交换文件，统一用 `zip` 最省事。

---

## 10. Git 版本控制

```bash
git init                # Initialize 当前目录初始化成 git 仓库
git clone <URL>         # 克隆远程仓库到本地
git status              # 查看工作区/暂存区状态 ← 最常用，先说它
git add <文件>          # ADD 把改动放入暂存区(staging)
git add .               # 暂存所有改动
git commit -m "说明"    # COMMIT 把暂存区固化成一次提交（快照）
git push                # 推送到远程
git pull                # 从远程拉取合并
git log                 # 查看提交历史（--oneline 精简）
git diff                # 查看未暂存的改动内容
git diff --cached       # 查看已暂存的改动
git branch              # 列出分支
git branch 新分支名      # 新建分支
git checkout <分支>      # 切换分支
git switch <分支>        # 切换分支（新版等价）
git merge <分支>         # 把分支合并到当前
git status --short      # 精简状态
git stash               # 临时保存未提交改动（腾出干净工作区）
git stash pop           # 恢复刚才的 stash
git reset --hard HEAD   # 丢弃所有未提交改动（**危险，会丢**）
```

**Git 三区概念**（理解的关键）：
| 区 | 含义 | 对应命令 |
|----|------|----------|
| 工作区 Working | 你正在编辑的文件 | （直接改） |
| 暂存区 Staging | 准备提交的改动 | `git add` |
| 仓库 Repo | 已固化的提交历史 | `git commit` |

> 流程模型：`改(工作区) → add(暂存区) → commit(仓库) → push(远程)`；
> 对应拉回：`pull(远程→本地) → checkout/merge(仓库→工作区)`。

---

## 11. Shell 脚本基础

创建一个 `hello.sh`：
```bash
#!/bin/bash                 # shebang：指明用 bash 解释执行
# 这是注释
name="Linux 用户"            # 变量赋值（等号两侧不能有空格）
echo "你好，$name"           # $ 取变量值
read -p "输入一个数字: " n   # 交互读入
echo "你输入的是 $n"

for i in 1 2 3; do          # for 循环
    echo "第 $i 次"
done

if [ $n -gt 10 ]; then       # if 判断（-gt 大于）
    echo "大于10"
else
    echo "小于等于10"
fi

date
```
运行方式：
```bash
chmod +x hello.sh      # 先加执行权限
./hello.sh             # 用 ./ 前缀执行（. 表示当前目录）
bash hello.sh          # 或直接指定解释器运行
```

**常用条件测试**：`-eq`等于 `-ne`不等 `-gt`大于 `-lt`小于 `-f 文件`存在文件 `-d`目录 `-e`存在。

---

## 12. 日常工作流（组合实战）

**场景 1：紧急排查"服务器内存/CPU 被谁占了"**
```bash
top                      # 看最耗资源的进程（记住 PID）
ps aux | sort -k3 -r | head -5   # 按 CPU 占用(%)第3列降序，取前5
ps aux | grep 进程名     # 锁定目标
kill -9 <PID>            # 强制终止
```

**场景 2：找出一堆文件里所有 TODO 并统计**
```bash
grep -rn "TODO" /project/src/
grep -rn "TODO" /project/src/ | wc -l   # 统计共有多少处
```

**场景 3：备份一个目录并打上时间戳**
```bash
tar -czf backup_$(date +%F).tar.gz myproject
# $(date +%F) 会展开成 2026-08-05，得到 backup_2026-08-05.tar.gz
```

**场景 4：查看某个程序日志的最新动向**
```bash
tail -f /var/log/程序.log
# Ctrl+C 停止；加 | grep error 可过滤：
tail -f /var/log/程序.log | grep -i error
```

**场景 5：批量改名（把 .txt 全改成 .md）**
```bash
for f in *.txt; do mv "$f" "${f%.txt}.md"; done
# ${f%.txt} 表示去掉结尾的 .txt
```

**场景 6：一键同步生产数据到备份目录并保留日志**
```bash
rsync -avh --progress /srv/data /srv/backup/
# rsync：Remote Sync，-a 归档 -v 显示 -h 人类可读
```

**场景 7：系统突然卡顿，查找磁盘占用大户**
```bash
du -sh /* 2>/dev/null | sort -h | tail -10   # 找出最大的前10个目录
df -h                                        # 别等满了才想起
```

---

## 13. 常用快捷键

| 快捷键 | 作用 | 说明 |
|--------|------|------|
| `Tab` | 命令/路径自动补全（按两下看所有匹配） | 最实用 |
| `Ctrl+C` | 中断当前命令（Interrupt） | — |
| `Ctrl+Z` | 挂起当前命令（Suspend，`fg` 恢复） | — |
| `Ctrl+D` | 退出 Shell / 发送 EOF | 空行按会退出登录 |
| `Ctrl+L` | 清屏（= `clear`） | — |
| `Ctrl+R` | 向后搜索历史命令（Reverse，再按继续往前翻） | — |
| `Ctrl+A` | 光标到行首（A=开头） | — |
| `Ctrl+E` | 光标到行尾（E=End） | — |
| `Ctrl+W` | 删除光标前一个词（Word） | — |
| `Ctrl+U` | 删除光标到行首的所有 | — |
| `Ctrl+K` | 删除光标到行尾（Kill） | — |
| `Ctrl+Y` | 粘回刚才删除的内容（Yank） | — |
| `Ctrl+T` | 交换光标前后两字符 | — |
| `↑/↓` | 上一条/下一条命令 | — |
| `!!` | 重复上一条命令 | bang bang |
| `!$` | 上一条命令的最后一个参数 | 如 `mkdir -p a` 后 `cd !$` |
| `!foo` | 执行最近一条以 foo 开头的命令 | — |
| `history` | 列出全部历史命令 | — |
| `df` 别名场景 | 少用 | — |

---

## 14. 命令命名规律与记忆技巧

1. **纯首字母缩写**（组合多个单词首字母）
   `pwd`=Print Working Directory，`rm`=Remove，`cp`=Copy，`mv`=Move，
   `mkdir`=MaKe+DIRectory，`cat`=conCATenate，`wc`=Word Count，
   `chmod`=CHange+MODe，`chown`=CHange+OWNer，`df`=Disk Free，`du`=Disk Usage。

2. **单词截断（取前几位）**
   `cd`=Change Directory→取首字母；`uname`=UNIX+NAME；`printf`=print formatted。

3. **表达功能意象（你能理解英文词就懂了）**
   `clear`清理、`history`历史、`sort`排序、`uniq`唯一、`grep`=Global Regular Expression Print。

4. **长选项规则**
   - 单横线+单字母：`-l`、`-h`、`-a`（每个字母=一个选项，可合并 `-lah`）
   - 双横线+完整单词：`--help`、`--verbose`、`--recursive`
   - 大小写敏感：`-r`(递归) ≠ `-R`(有时也递归，各命令不同)

5. **如何快速自学任何新命令**
   ```bash
   命令 --help     # 简洁用法
   man 命令         # manual 完整手册（q 退出，/ 搜索）
   whatis 命令      # 一句话说明
   info 命令        # 更详细的 info 文档
   ```

---

## 附：常见 `apt` 与 C++ 开发相关的快捷备忘
```bash
sudo apt install build-essential   # gcc/g++/make 全套编译器
sudo apt install cmake             # CMake（本项目构建用）
sudo apt install git               # 版本控制
sudo apt install htop              # 增强进程监控
sudo apt install tree 目录          # 树状显示目录结构
tree -L 2                          # 只看两级
```

---

*祝你变得更强。善用 `man` 与 `--help`，再复杂的系统也敌不过循序渐进的积累。*