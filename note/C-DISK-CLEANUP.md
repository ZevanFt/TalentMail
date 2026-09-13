# C 盘清理参考（只读分析，执行前请自行确认）

> 分析环境：Windows，C: 剩余约 33 GB

## 建议优先清理（相对安全）

| 路径 | 约占用 | 说明 | 风险 |
|------|--------|------|------|
| `%LOCALAPPDATA%\Temp` | ~1.0 GB | 临时文件 | 低（正被占用的会跳过） |
| `%LOCALAPPDATA%\npm-cache` | ~194 MB | npm 缓存，`npm cache clean --force` | 低 |
| `%LOCALAPPDATA%\pip\Cache` | （若存在） | pip 缓存 | 低 |
| `C:\Windows\SoftwareDistribution\Download` | ~213 MB | Windows 更新下载残留 | 低 |
| Edge/Chrome Cache | ~277 MB | 浏览器缓存 | 低，会自动重建 |

估算可回收：**约 1.5–2 GB**（不含 Downloads）

## 需要您自己翻的

| 路径 | 约占用 | 说明 |
|------|--------|------|
| `Downloads` | **~4.4 GB** | 个人下载，最大头；请手动筛选安装包/大文件 |
| `%LOCALAPPDATA%\.cache\codex-runtimes` | **~1.3 GB** | 某些工具运行时缓存，确认不用可删 |
| `%LOCALAPPDATA%\Packages` | ~2.0 GB | UWP/WSL 相关，**不要整目录删** |

## 不建议动

- `C:\ProgramData\Package Cache`（~159 MB）— 安装器缓存，删了可能无法卸载/修复软件  
- `C:\Windows\*` 系统目录（除 SoftwareDistribution\Download）  
- `Packages` 里的系统应用容器  

## 清理后 Docker 建议

1. 目标：C 盘自由空间 **≥ 40 GB** 更稳妥  
2. Docker Desktop 程序仍装默认位置（C:，约 2–4 GB）  
3. **Disk image location** 改为 `G:\docker-data`  
4. 镜像/容器/邮件栈数据全部落 G:  

## 示例命令（管理员 PowerShell，确认后再跑）

```powershell
# 清用户 Temp（7 天前）
Get-ChildItem "$env:LOCALAPPDATA\Temp" -Recurse -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# npm 缓存
npm cache clean --force

# Windows 更新下载（需停 wuauserv）
Stop-Service wuauserv -Force
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
Start-Service wuauserv
```

**删除前请自行备份或确认；本文件仅作分析记录。**
