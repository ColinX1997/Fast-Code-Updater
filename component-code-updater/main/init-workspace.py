import os
import requests
from bs4 import BeautifulSoup
import subprocess
import shutil
from datetime import datetime
import re
from packaging import version


local_folder_path = r"C:\MES-Component\_workspace\IPS_C\FAST"
version_output_file = local_folder_path + "\\component_versions.txt"
seven_zip_path = r"C:\Program Files\7-Zip\7z.exe"
url = "https://fast.bmw-brilliance.cn/integration/pcs21/gen6/"
# url = "https://fast.bmw-brilliance.cn/integration/pcs21/tek/"


# Download required files in certain verison - from component_versions.txt
def download_certain_versions():
    data_dict = {}
    with open(version_output_file, "r") as file:
        lines = file.readlines()
        data_dict = {
            line.strip().split(": ")[0]: line.strip().split(": ")[1] for line in lines
        }
    for file_name, version in data_dict.items():
        file_path = os.path.join(local_folder_path, file_name)
        if not os.path.exists(file_path):
            get_remote_files(file_name, version)
        else:
            print(
                file_name,
                " exist already, use updater for this component instead of init tool",
            )


def get_remote_files(name, version):
    # 发送HTTP请求
    response = requests.get(url)
    response.raise_for_status()  # 确保请求成功

    # 解析HTML
    soup = BeautifulSoup(response.content, "html.parser")

    # 查找所有 <a> 标签
    links = soup.find_all("a", href=True)

    remote_files = [
        link["href"]
        for link in links
        if name in link["href"] and version in link["href"]
    ]
    print(remote_files)
    if len(remote_files) > 0:
        if not os.path.exists(local_folder_path):
            os.makedirs(local_folder_path)

        remote_url = f"{url}/{remote_files[0]}"
        download_file_path = os.path.join(local_folder_path, name + ".rpm")

        # 下载文件
        response = requests.get(remote_url)
        response.raise_for_status()  # 确保请求成功

        with open(download_file_path, "wb") as f:
            f.write(response.content)

        print(f"正在下载: {name}  {version}")

        extract_to_version_folder(download_file_path, name, version)


def extract_to_version_folder(rpm_path, name, version):
    # 使用7-zip解压文件
    extract_rpm_to_path = os.path.join(local_folder_path, name)
    if not os.path.exists(extract_rpm_to_path):
        os.makedirs(extract_rpm_to_path)
    subprocess.run(
        [
            seven_zip_path,
            "x",
            rpm_path,
            "-o" + extract_rpm_to_path,
            "-y",
        ],
        check=True,
    )
    print(f"已解压并删除RPM: {name}")
    os.remove(rpm_path)
    extract_cpio_files(extract_rpm_to_path, version)


def extract_cpio_files(extract_rpm_to_path, version):
    # 获取下载文件夹中的所有文件
    files = os.listdir(extract_rpm_to_path)

    for file_name in files:
        if file_name.endswith(".cpio"):
            rpm_file_path = os.path.join(extract_rpm_to_path, file_name)
            # 使用7-zip解压cpio文件
            subprocess.run(
                [seven_zip_path, "x", rpm_file_path, "-o" + extract_rpm_to_path, "-y"],
                check=True,
            )
            print(f"已解压cpio文件: {file_name} 到 {extract_rpm_to_path}, 并删除CPIO")
            os.remove(rpm_file_path)


def git_init_all_folders():
    # 遍历指定路径下的所有文件夹
    for folder_name in os.listdir(local_folder_path):
        folder_path = os.path.join(local_folder_path, folder_name)

        # 检查是否为文件夹
        if os.path.isdir(folder_path):
            # 构建git init命令
            command = ["git", "init"]

            # 切换到文件夹路径
            os.chdir(folder_path)
            create_gitignore(folder_path)
            if not os.path.exists(".git"):
                # 调用git init命令
                try:
                    result = subprocess.run(
                        command,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    print(f"成功初始化 {folder_path}")
                    print(result.stdout.decode())
                except subprocess.CalledProcessError as e:
                    print(f"初始化 {folder_path} 失败")
                    print(e.stderr.decode())

                try:
                    subprocess.run(["git", "add", "."], check=True)
                    print(f"成功添加所有文件到暂存区 {folder_path}")
                except subprocess.CalledProcessError as e:
                    print(f"添加文件到暂存区 {folder_path} 失败")
                    print(e.stderr.decode())
                    continue

                # 执行git commit
                try:
                    subprocess.run(["git", "commit", "-m", "Init Commit"], check=True)
                    print(f"成功提交初始文件 {folder_path}")
                except subprocess.CalledProcessError as e:
                    print(f"提交初始文件 {folder_path} 失败")
                    print(e.stderr.decode())
            else:
                print("Git Init already for: ", folder_name)


def create_gitignore(directory):
    # 指定 .gitignore 文件的路径
    gitignore_path = os.path.join(directory, ".gitignore")

    # 检查文件是否存在，如果存在则不进行创建
    if os.path.exists(gitignore_path):
        print(f"{gitignore_path} 已存在，不会覆盖已有文件。")
        return
    else:
        # 创建 .gitignore 文件
        with open(gitignore_path, "w") as file:
            # 写入 *.pyc
            file.write("*.pyc\n")

        print(f"已成功创建 {gitignore_path} 文件并添加了 *.pyc。")


download_certain_versions()
git_init_all_folders()
