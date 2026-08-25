# gitee终端指令

### **常用指令**

```bash
# 1. 初始化并关联远程仓库
git init
git remote add origin https://gitee.com/你的用户名/仓库名.git

# 2. 添加文件并提交
git add .
git commit -m "Initial commit"

# 3. 推送到远程 main 分支
git push -u origin main
```

### **1. 初始化与基础配置**

```bash
# 初始化本地仓库（项目目录下运行）
git init

# 设置用户名和邮箱（提交时显示作者信息）
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"

# 查看当前配置
git config --list
```

### **2. 本地仓库操作**

```bash
# 查看当前文件状态（红色未跟踪，绿色已暂存）
git status

# 添加所有文件到暂存区
git add .

# 添加单个文件到暂存区
git add 文件名

# 提交到本地仓库
git commit -m "提交描述"

# 查看提交历史（简洁版）
git log --oneline

# 撤销工作区的修改（未 add 的文件）
git checkout -- 文件名

# 撤销暂存区的修改（已 add 未 commit）
git reset HEAD 文件名
```

### **3. 分支管理**

```bash
# 查看所有分支（* 号指向当前分支）
git branch -a

# 创建新分支
git branch 分支名

# 切换分支
git checkout 分支名

# 创建并切换分支（一步到位）
git checkout -b 分支名

# 合并分支（先切换到目标分支）
git merge 被合并的分支名

# 删除本地分支
git branch -d 分支名
```

### **4. 远程仓库操作（Gitee/GitHub）**

```bash
# 关联远程仓库（首次）
git remote add origin https://gitee.com/你的用户名/仓库名.git

# 查看远程仓库关联状态
git remote -v

# 克隆远程仓库
git clone https://gitee.com/你的用户名/仓库名.git

# 推送本地分支到远程（首次需加 -u）
git push -u origin 分支名

# 强制推送（谨慎使用！会覆盖远程代码）
git push -f origin 分支名

# 拉取远程分支最新代码
git pull origin 分支名

# 从远程创建本地分支并切换
git checkout -b 本地分支名 origin/远程分支名
```

### **5. 冲突解决**

```bash	
# 拉取远程代码时自动合并（若无冲突）
git pull

# 手动解决冲突后标记为已解决
git add 冲突文件
git commit -m "解决冲突"
```

### **6. 版本回退**

```bash
# 查看所有提交记录（含 commit id）
git log

# 回退到指定 commit（保留修改）
git reset --soft commit_id

# 回退到指定 commit（丢弃修改）
git reset --hard commit_id

# 强制推送到远程（回退后需覆盖远程）
git push -f origin 分支名

```

### **7. 其他实用命令**

```bash
# 查看文件改动内容（对比工作区和暂存区）
git diff

# 暂存当前修改（临时切换分支时用）
git stash
git stash pop  # 恢复暂存内容

# 删除远程分支
git push origin --delete 分支名
```

### **完整工作流示例（提交到 Gitee）**	

```bash
# 1. 初始化并关联远程仓库
git init
git remote add origin https://gitee.com/你的用户名/仓库名.git

# 2. 添加文件并提交
git add .
git commit -m "Initial commit"

# 3. 推送到远程 main 分支
git push -u origin main
```

