# Windows 本地制作

## 立即观看现有样片

解压整个下载包。打开 `preview/body-preview.mp4` 即可观看现有40秒无声预览。
可以将该文件复制到 `C:\Users\24463\OneDrive\Video`。
这只是排版和制作流程测试样片，尚未获得分镜或视频批准。

## 在本机重新生成

1. 把程序解压到普通本地文件夹，例如 `C:\Users\24463\VideoMaker`。
2. 确认 `C:\Users\24463\OneDrive\Video` 已存在。
3. 双击 `setup-windows.cmd`。它通过 winget 安装缺少的 Python 3.12、FFmpeg，
   在程序目录建立 Python 虚拟环境，并安装 Playwright 和 Chromium。
   第一次安装 Python 后，需要关闭窗口，再运行一次 setup-windows.cmd。
   需要联网下载依赖；公司设备若限制安装，应由公司 IT 安装这些工具。
4. 安装成功后双击 `run-preview.cmd`。
5. 程序在 `%USERPROFILE%\OneDrive\Video\Preview-日期时间\` 生成视频，自动用系统播放器打开。
   每次生成一个新文件夹，不覆盖旧视频。

只有 OneDrive 客户端正在运行、已登录且此目录处于同步范围时，文件才会自动上传。
程序保存成功并不代表云端同步完成，请检查文件旁的 OneDrive 同步状态。

本地预览无需密钥。当前演示为40秒无声文字画面，不包含片头片尾、图解动画或自动配音。
Notion/AI/审核状态自动化仍需另外配置；这些启动文件不会启动定时任务或调用收费 API。

代码已在 Linux 验证渲染和媒体时长，尚未在真实 Windows 机器执行；需要首次本机运行验证。
