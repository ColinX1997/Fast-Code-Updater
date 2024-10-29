import os
import requests
from bs4 import BeautifulSoup
import subprocess
import shutil
from datetime import datetime
import re
from packaging import version


# 网页URL, 对于不同文件存在多个可能地址：https://fast.bmw-brilliance.cn/integration/pcs21/tek/，gen6/, common/
url = "https://fast.bmw-brilliance.cn/integration/pcs21/gen6/"
# url = "https://fast.bmw-brilliance.cn/integration/pcs21/tek/"

# 本地文件夹路径
local_folder_path = r"C:\MES-Component\_workspace\IPS_C\FAST"
version_output_file = local_folder_path + "\\component_versions.txt"
seven_zip_path = r"C:\Program Files\7-Zip\7z.exe"

local_files_version = {}


def get_local_files(folder_path):
    # 获取本地文件夹中的文件名
    local_files = os.listdir(folder_path)
    return local_files


def get_remote_files(url, local_files):
    # 发送HTTP请求
    response = requests.get(url)
    response.raise_for_status()  # 确保请求成功

    # 解析HTML
    soup = BeautifulSoup(response.content, "html.parser")

    # 查找所有 <a> 标签
    links = soup.find_all("a", href=True)
    all_latest_remote_files = []
    for local_file in local_files:
        # 筛选包含特定关键字的链接
        remote_files = [link["href"] for link in links if local_file in link["href"]]
        # 保留每个文件的最后一个版本
        if len(remote_files) > 0:
            to_update = keep_latest_version(remote_files)
            if to_update is not None:
                all_latest_remote_files.append(to_update)
    return all_latest_remote_files


def keep_latest_version(file_list):
    component_versions = extract_version(file_list, "version")
    max_version = max(component_versions, key=version.parse)
    for file in file_list:
        if max_version in file:
            return file
    return None


def find_updates(local_files, remote_files):
    # 找到需要更新的文件
    updates = []
    latest_files_version = extract_version(remote_files, "name_version")
    for file, version in local_files.items():
        if file in latest_files_version and latest_files_version[file] != version:
            updates.append(
                (file + " " + version, find_remote_file_name(file, remote_files))
            )

    return updates


def find_remote_file_name(file_name, remote_files):
    for remote_file in remote_files:
        if file_name in remote_file:
            return remote_file
    return None


def download_files(updates):
    # 确保下载文件夹存在
    if not os.path.exists(local_folder_path):
        os.makedirs(local_folder_path)

    for local_file, remote_file in updates:
        name = str(local_file).split()[0]
        remote_url = f"{url}/{remote_file}"
        download_file_path = os.path.join(local_folder_path, remote_file)

        # 下载文件
        response = requests.get(remote_url)
        response.raise_for_status()  # 确保请求成功

        with open(download_file_path, "wb") as f:
            f.write(response.content)

        print(f"正在下载: {remote_file}")

        project_version = extract_version([remote_file], "name_version")
        extract_to_version_folder(download_file_path, name, project_version[name])


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
            # 创建Version文件夹
            extract_cpio_to_path = os.path.join(extract_rpm_to_path, version)
            if not os.path.exists(extract_cpio_to_path):
                os.makedirs(extract_cpio_to_path)
            # 使用7-zip解压cpio文件
            subprocess.run(
                [seven_zip_path, "x", rpm_file_path, "-o" + extract_cpio_to_path, "-y"],
                check=True,
            )
            print(f"已解压cpio文件: {file_name} 到 {extract_cpio_to_path}, 并删除CPIO")
            os.remove(rpm_file_path)
            git_add(extract_rpm_to_path, version)


def git_add(extract_rpm_to_path, verison):
    # 执行git commit -A
    os.chdir(extract_rpm_to_path)
    try:
        subprocess.run(["git", "add", "--all"], check=True)
        print(f"成功添加所有改动文件到暂存区 {extract_rpm_to_path}")
    except subprocess.CalledProcessError as e:
        print(f"添加改动文件 {extract_rpm_to_path} 失败")

    # 执行git commit
    try:
        subprocess.run(["git", "commit", "-m", verison], check=True)
        print(f"成功提交改动文件 {extract_rpm_to_path}")
    except subprocess.CalledProcessError as e:
        print(f"提交改动文件 {extract_rpm_to_path} 失败")

    # 执行git add tag
    try:
        subprocess.run(
            ["git", "tag", "-a", "V-" + verison, "-m", "V-" + verison], check=True
        )
        print(f"成功添加版本Tag {verison}")
    except subprocess.CalledProcessError as e:
        print(f"添加版本Tag {verison} 失败")


def extract_version(file_list, type):
    pattern = re.compile(r"^(?P<project_name>[^-]+)-(?P<version>[^-\s]+)-(?P<arch>.+)$")
    project_name_versions = {}
    project_versions = []
    for file_name in file_list:
        if str(file_name).count("-") > 2:
            version = str(file_name).split("-")[-2]
            sub_version = str(file_name).split("-")[-1]
            project_name = (
                str(file_name).replace("-" + version, "").replace("-" + sub_version, "")
            )
            version += "-" + sub_version.split(".")[0]
        else:
            # 使用正则表达式提取项目名和版本号
            match = pattern.match(file_name)
            if match:
                project_name = match.group("project_name")
                version = match.group("version")
                arch = match.group("arch")
                # 检查版本号后是否有 -3
                version += "-" + arch.split(".")[0]
        project_name_versions[project_name] = version
        project_versions.append(version)
    if type == "name_version":
        return project_name_versions
    else:
        return project_versions


def record_version(local_files_version, update_files):
    project_versions = extract_version(
        [remote_file for local_file, remote_file in update_files], "name_version"
    )
    for file, version in project_versions.items():
        local_files_version[file] = version

    # 将结果写入文件
    with open(version_output_file, "w") as f:
        for project, version in local_files_version.items():
            f.write(f"{project}: {version}\n")

    print(f"项目和版本信息已写入 {version_output_file}")


def read_versions():
    with open(version_output_file, "r") as file:
        lines = file.readlines()
        data_dict = {
            line.strip().split(": ")[0]: line.strip().split(": ")[1] for line in lines
        }
    return data_dict


def main():
    # 获取本地文件列表
    local_files = get_local_files(local_folder_path)

    # 获取远程文件列表
    remote_files_to_update = get_remote_files(url, local_files)

    # # 找到需要更新的文件
    local_files_version = read_versions()
    updates = find_updates(local_files_version, remote_files_to_update)

    if updates:
        # 输出需要更新的文件列表
        for local_file, remote_file in updates:
            print(f"需要更新: {local_file} -> {remote_file}")

        # 下载需要更新的文件
        download_files(updates)

        # 更新新文件版本
        record_version(local_files_version, updates)

    else:
        print("所有文件已经是最新版本")


if __name__ == "__main__":
    main()
