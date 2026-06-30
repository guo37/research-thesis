# 多设备同步

目标设备：

- 家用 Windows
- 办公 Windows
- 出门使用的 Mac

本研究工作空间以 Git 作为同步基准。每台设备都应把同一个私有仓库克隆到本地研究目录。不要把这个 Git 仓库放进云盘自动同步目录。

## 第一台设备的一次性设置

```powershell
git init
git branch -M main
git lfs install
git add .
git commit -m "Initialize research workspace"
git remote add origin <private-repo-url>
git push -u origin main
```

## 其他 Windows 设备的一次性设置

```powershell
git clone <private-repo-url> E:\Research\reserach
cd E:\Research\reserach
git lfs install
```

如果目标路径不同，应在个人工作空间索引中记录实际路径。

## Mac 的一次性设置

```bash
git clone <private-repo-url> ~/Research/reserach
cd ~/Research/reserach
git lfs install
```

## 开始工作

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_start.ps1
```

在 Mac 上：

```bash
bash scripts/sync_start.sh
```

该命令会用 rebase 方式拉取远端变更，并显示本地状态。

## 结束工作

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_finish.ps1 -Message "your commit message"
```

在 Mac 上：

```bash
bash scripts/sync_finish.sh "your commit message"
```

该命令会检查被忽略的敏感文件、暂存允许提交的变更、创建提交，并在存在远端时推送。

## 冲突规则

切换设备前，必须确保 `git status` 干净。如果两台设备修改了同一个 Markdown 文件，先拉取，然后在发现冲突的设备上立即解决。
