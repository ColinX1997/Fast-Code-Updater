import re


def rename_file(filename):
    # 使用正则表达式匹配版本号前的所有字符和连字符
    # 然后将这些连字符替换为下划线
    new_name = re.sub(r"(.*)-(\d+\.\d+\.\d+)-(\d+)", r"\1_\2-\3", filename)
    return new_name


# 测试示例
filenames = [
    "ipsc-gen6-em-standard-messages-1.2.1-2.noarch",
    "ipsc-resor-0.0.1-1.noarch",
]
for filename in filenames:
    print(rename_file(filename))
