import requests
from bs4 import BeautifulSoup

# 网页URL
url = "https://fast.bmw-brilliance.cn/integration/pcs21/gen6/"


def get_links(url, keyword):
    # 发送HTTP请求
    response = requests.get(url)
    response.raise_for_status()  # 确保请求成功

    # 解析HTML
    soup = BeautifulSoup(response.content, "html.parser")

    # 查找所有 <a> 标签
    links = soup.find_all("a", href=True)

    # 筛选包含特定关键字的链接
    filtered_links = [link["href"] for link in links if keyword in link["href"]]

    return filtered_links


def main():
    keyword = "all_gen6_elf"  # 你指定的关键字
    links = get_links(url, keyword)
    print(f"Found {len(links)} links containing the keyword '{keyword}':")
    for link in links:
        print(link)


if __name__ == "__main__":
    main()
