import os

# 定义文件路径
url_file = r"E:\FILES\WorkSpace\Coding\project\songSim\StyleListTabDelimited2downloadList.txt"  # 存储 URL 的文件
downloaded_file = r"E:\FILES\WorkSpace\Coding\project\songSim\names_output.txt"  # 存储已下载文件名称的文件
output_file = r"E:\FILES\WorkSpace\Coding\project\songSim\not_downloaded.txt"  # 存储未下载的 URL 的文件

# 读取已下载的文件名称
def read_downloaded_files(filename):
    with open(filename, 'r') as f:
        return set(line.strip() for line in f)

# 读取 URL 文件并检查哪些文件尚未下载
def find_not_downloaded_urls(url_filename, downloaded_filenames):
    not_downloaded_urls = []
    with open(url_filename, 'r') as f:
        for url in f:
            url = url.strip()
            filename = url.split('/')[-1]  # 从 URL 中提取文件名
            if filename not in downloaded_filenames:
                not_downloaded_urls.append(url)
    return not_downloaded_urls

# 将未下载的 URL 写入到输出文件
def write_not_downloaded_urls(not_downloaded_urls, output_filename):
    with open(output_filename, 'w') as f:
        for url in not_downloaded_urls:
            f.write(url + '\n')

def main():
    # 读取已下载的文件名
    downloaded_filenames = read_downloaded_files(downloaded_file)
    
    # 查找未下载的 URL
    not_downloaded_urls = find_not_downloaded_urls(url_file, downloaded_filenames)
    
    # 将未下载的 URL 写入到输出文件
    write_not_downloaded_urls(not_downloaded_urls, output_file)
    
    print(f"未下载的 URL 已保存到 {output_file}")

if __name__ == "__main__":
    main()
