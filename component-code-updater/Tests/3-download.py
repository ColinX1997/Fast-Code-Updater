import os
import requests
from bs4 import BeautifulSoup

# 网页URL
url = "https://fast.bmw-brilliance.cn/integration/pcs21/gen6/"
# 本地文件夹路径
local_folder_path = r"C:\MES-Component\_workspace\IPS_C\FAST"
download_folder_path = r"C:\MES-Component\_workspace\IPS_C\FAST"


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


def download_files(updates, download_folder_path):
    # 确保下载文件夹存在
    if not os.path.exists(download_folder_path):
        os.makedirs(download_folder_path)

    for local_file, remote_file in updates:
        remote_url = f"{url}/{remote_file}"
        local_file_path = os.path.join(download_folder_path, remote_file)

        # 下载文件
        response = requests.get(remote_url)
        response.raise_for_status()  # 确保请求成功

        with open(local_file_path, "wb") as f:
            f.write(response.content)

        print(f"已下载: {remote_file}")


def main():
    # 获取远程文件列表
    remote_files = get_remote_files(url, "all_gen6_elf")

    # 获取本地文件列表
    local_files = get_local_files(local_folder_path)

    # 找到需要更新的文件
    updates = find_updates(local_files, remote_files)

    # 输出需要更新的文件列表
    for local_file, remote_file in updates:
        print(f"需要更新: {local_file} -> {remote_file}")

    # 下载需要更新的文件
    download_files(updates, download_folder_path)


if __name__ == "__main__":
    main()
