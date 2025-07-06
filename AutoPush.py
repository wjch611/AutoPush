import os
import subprocess
import argparse
from datetime import datetime
import shlex

def run_git_command(cmd, cwd):
    """执行Git命令并处理错误"""
    try:
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
            
        result = subprocess.run(
            cmd, 
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            error_output = result.stderr.strip()
            print(f"错误: {' '.join(cmd)}\n{result.stdout.strip()}\n{error_output}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return None

def ensure_ssh_remote(repo_dir):
    """确保远程使用SSH协议"""
    # 获取当前远程URL
    remote_url = run_git_command("git remote get-url origin", repo_dir)
    
    if not remote_url:
        print("无法获取远程URL")
        return False
    
    # 检查是否已经是SSH URL
    if remote_url.startswith("git@github.com:"):
        print(f"远程已使用SSH: {remote_url}")
        return True
    
    # 转换HTTPS URL为SSH URL
    if remote_url.startswith("https://github.com/"):
        ssh_url = remote_url.replace(
            "https://github.com/", 
            "git@github.com:"
        ).replace(".git", "") + ".git"
        
        # 设置新的SSH远程
        if run_git_command(f"git remote set-url origin {ssh_url}", repo_dir) is not None:
            print(f"已将远程URL更改为SSH: {ssh_url}")
            return True
        return False
    
    print(f"无法识别的远程URL格式: {remote_url}")
    return False

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Git自动提交脚本')
    parser.add_argument('-d', '--dir', default=os.path.expanduser("~/notes"), 
                        help='Git仓库路径 (默认: ~/notes)')
    parser.add_argument('-b', '--branch', default='main', 
                        help='目标分支名 (默认: main)')
    args = parser.parse_args()

    repo_dir = os.path.abspath(os.path.expanduser(args.dir))
    branch = args.branch

    # 验证目录是否存在
    if not os.path.exists(repo_dir):
        print(f"错误：目录不存在 - {repo_dir}")
        exit(1)

    # 检查仓库
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        print(f"错误：{repo_dir} 不是Git仓库")
        exit(1)
    
    # 确保使用SSH远程
    if not ensure_ssh_remote(repo_dir):
        print("⚠️ 无法配置SSH远程，将继续尝试")

    # 检查变更
    status = run_git_command("git status --porcelain", repo_dir)
    if not status:
        print("没有检测到文件变更，跳过提交")
        exit(0)

    # 执行提交
    commit_msg = f"自动提交: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    print(f"检测到文件变更，正在提交 {repo_dir} 到分支 {branch}...")

    # 添加所有变更
    if run_git_command("git add .", repo_dir) is None:
        print("添加文件失败")
        exit(1)
    
    # 提交变更
    commit_cmd = ["git", "commit", "-q", "-m", commit_msg]
    if run_git_command(commit_cmd, repo_dir) is None:
        print("提交失败")
        exit(1)
    
    # 推送变更
    push_cmd = f"git push -q origin {branch}"
    push_result = run_git_command(push_cmd, repo_dir)
    
    if push_result is None:
        print("\n推送失败，请检查以下配置：")
        print("1. 确保已添加SSH密钥到GitHub")
        print("2. 测试SSH连接: ssh -T git@github.com")
        print("3. 手动推送一次: git push origin main")
        print("4. 如果问题持续，请访问 https://github.com/settings/keys")
        exit(1)

    commit_hash = run_git_command("git rev-parse --short HEAD", repo_dir)
    print(f"✅ 提交成功！最新版本: {commit_hash}")

if __name__ == "__main__":
    main()