import requests

def Download(url, path):
    #下载图片
    response = requests.get(url)
    if response.status_code == 200:
        with open(path ,"wb") as f:
            f.write(response.content)
    else:
        print("下载失败")