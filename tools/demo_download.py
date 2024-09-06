import os
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# 配置部分
URL_FILE = 'E:\FILES\WorkSpace\Coding\project\songSim\StyleListTabDelimited2output.txt'  # 包含 URL 的文件
DOWNLOAD_DIR = 'E:\FILES\WorkSpace\Coding\project\songSim\demoMusic'  # 下载内容的目录
MAX_THREADS = 10  # 最大线程数

# 确保下载目录存在
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_file(url):
    try:
        # 从 URL 中提取文件名
        filename = os.path.basename(url)
        file_path = os.path.join(DOWNLOAD_DIR, filename)

        # 下载文件
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 如果响应状态码不是 200，将抛出异常

        # 获取文件总大小（字节）
        total_size = int(response.headers.get('content-length', 0))

        # 写入文件并显示进度条
        with open(file_path, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            ascii=True
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))

        print(f"下载完成: {file_path}")

    except Exception as e:
        print(f"下载失败 ({url}): {e}")

def main():
    with open(URL_FILE, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # 使用 tqdm 进度条显示总进度
        list(tqdm(executor.map(download_file, urls), total=len(urls), desc="总进度"))

if __name__ == '__main__':
    main()
