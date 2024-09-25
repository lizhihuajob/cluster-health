import requests
from bs4 import BeautifulSoup

# 检查网络连接
def check_internet(url='https://plugins.jetbrains.com'):
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Internet connection is working.")
    except requests.RequestException as e:
        print("Internet connection error:", e)

# 使用BeautifulSoup检查插件仓库是否可访问
def check_plugin_repository(url='https://plugins.jetbrains.com'):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup)
        # 检查页面元素，例如查找包含"JetBrains"的文本
        if soup.find(string='JetBrains') is not None:
            print("Plugin repository is accessible.")
        else:
            print("Plugin repository may have issues.")
    except requests.RequestException as e:
        print("Error accessing plugin repository:", e)


def check_test_object():
    #connection_pairs = list(zip(connections[: len(connections) // 2], connections[len(connections) // 2:]))
    #num01 = 3
    #print(num01//2)
    connections = ["1","2","3","4","5","6","7"]
    print(connections)
    
    print(connections[: len(connections) // 2])
    print(connections[len(connections) // 2 :])
    
    connection_pairs = list(zip(connections[: len(connections) // 2], connections[len(connections) // 2 :]))

def check_test_002():
    print("check test 002")
    groups = ["a","b"]
    group_and_rail = [(group, rail) for group in groups for rail in range(8)]
    print(group_and_rail)
    pass
# 主函数
def main():
    #check_internet()
    #check_plugin_repository()
    #check_test_object()
    check_test_002()
if __name__ == "__main__":
    main()
