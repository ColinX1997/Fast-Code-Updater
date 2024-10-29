import os
import requests
from bs4 import BeautifulSoup
import subprocess
import shutil
from datetime import datetime
import time


# 网页URL
url = "https://fast.bmw-brilliance.cn/integration/pcs21/gen6/"
# 本地文件夹路径
local_folder_path = r"C:\MES-Component\_workspace\IPS_C\FAST"
seven_zip_path = r"C:\Program Files\7-Zip\7z.exe"


def get_remote_files(url, keyword):
    # 发送HTTP请求
    response = requests.get(url)
    response.raise_for_status()  # 确保请求成功

    # 解析HTML
    soup = BeautifulSoup(response.content, "html.parser")

    # 查找所有 <a> 标签
    links = soup.find_all("a", href=True)

    # 筛选包含特定关键字的链接
    remote_files = [link["href"] for link in links if keyword in link["href"]]

    # 保留每个文件的最后一个版本
    remote_files = keep_latest_versions(remote_files)

    return remote_files


def keep_latest_versions(file_list):
    # 用于存储每个文件的最后一个版本
    latest_versions = {}

    for file_name in file_list:
        base_name = file_name.split("-")[0]
        latest_versions[base_name] = file_name

    # 只保留最后一个版本的文件名
    return list(latest_versions.values())


def get_local_files(folder_path):
    # 获取本地文件夹中的文件名
    local_files = os.listdir(folder_path)
    return local_files


def find_updates(local_files, remote_files):
    # 找到需要更新的文件
    updates = []
    for local_file in local_files:
        base_name = local_file.split("-")[0]
        remote_file = next((f for f in remote_files if f.startswith(base_name)), None)
        if remote_file and local_file != str(remote_file).replace(".rpm", ""):
            updates.append((local_file, remote_file))

    return updates


def download_files(updates, local_folder_path):
    # 确保下载文件夹存在
    if not os.path.exists(local_folder_path):
        os.makedirs(local_folder_path)

    for local_file, remote_file in updates:
        remote_url = f"{url}/{remote_file}"
        local_file_path = os.path.join(local_folder_path, remote_file)

        # 下载文件
        response = requests.get(remote_url)
        response.raise_for_status()  # 确保请求成功

        with open(local_file_path, "wb") as f:
            f.write(response.content)

        print(f"正在下载: {remote_file}")


def unzip_files(local_folder_path, seven_zip_path):
    # 获取下载文件夹中的所有文件
    files = os.listdir(local_folder_path)

    for file_name in files:
        if file_name.endswith(".rpm"):
            file_path = os.path.join(local_folder_path, file_name)
            # 使用7-zip解压文件
            subprocess.run(
                [seven_zip_path, "x", file_path, "-o" + local_folder_path, "-y"],
                check=True,
            )
            print(f"已解压并删除RPM: {file_name}")
            os.remove(file_path)
            # 继续解压cpio文件
        extract_cpio_files(local_folder_path, seven_zip_path)


def extract_cpio_files(local_folder_path, seven_zip_path):
    # 获取下载文件夹中的所有文件
    files = os.listdir(local_folder_path)

    for file_name in files:
        if file_name.endswith(".cpio"):
            file_path = os.path.join(local_folder_path, file_name)
            # 创建同名文件夹
            output_folder = os.path.join(
                local_folder_path, str(file_name).replace(".cpio", "")
            )
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            # 使用7-zip解压cpio文件
            subprocess.run(
                [seven_zip_path, "x", file_path, "-o" + output_folder, "-y"], check=True
            )
            print(f"已解压cpio文件: {file_name} 到 {output_folder}, 并删除CPIO")
            os.remove(file_path)


def get_modification_date(path):
    return datetime.fromtimestamp(os.path.getmtime(path))


def parse_folder_name(name):
    return name.split("-")[0]


def delete_old_folders(directory):
    # 用于存储文件夹信息的字典，键为文件夹名称的第一部分，值为包含路径和修改日期的元组
    folders = {}
    # 只检查指定目录的直接子目录
    for dir in os.listdir(directory):
        path = os.path.join(directory, dir)
        if os.path.isdir(path):
            name = parse_folder_name(dir)
            mod_date = get_modification_date(path)
            if name not in folders:
                # 更新需要的文件目录
                folders[name] = (path, mod_date)
            elif mod_date > folders[name][1]:
                # 删除旧的文件夹
                old_folder = folders[name][0]
                folders[name] = (path, mod_date)
                old_folder = os.path.normpath(old_folder)
                print(old_folder, os.path.exists(old_folder))
                if os.path.exists(old_folder):
                    try:
                        print(f"删除旧目录: {path}")
                        shutil.rmtree(path, ignore_errors=False)
                    except FileNotFoundError:
                        try:
                            print(f"文件或目录未找到, 移至TrashPycData目录中")
                            os.chdir(local_folder_path)
                            os.makedirs("TrashPycData", exist_ok=True)
                            shutil.move(path, "TrashPycData")
                            os.rename(path, "TrashPycData")
                        except Exception:
                            pass


def main():
    # 获取远程文件列表
    remote_files = get_remote_files(url, "all_gen6_elf")

    # 获取本地文件列表
    local_files = get_local_files(local_folder_path)

    # 找到需要更新的文件
    updates = find_updates(local_files, remote_files)

    if updates:
        # 输出需要更新的文件列表
        # for local_file, remote_file in updates:
        #     print(f"需要更新: {local_file} -> {remote_file}")

        # # 下载需要更新的文件
        # download_files(updates, local_folder_path)

        # # 解压下载的文件
        # unzip_files(local_folder_path, seven_zip_path)

        # 删除旧版本的文件夹
        print("st detek")
        delete_old_folders(local_folder_path)
    else:
        print("所有文件已经是最新版本")


if __name__ == "__main__":
    main()
