from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
from webdriver_manager.chrome import ChromeDriverManager

from yidun_verify.predict import YOLO_Predict

#推理逻辑
class Verification():
    def __init__(self, url, tips):
        self.url = url
        self.download_folder = "yidun_verify/images/"
        self.tips = tips
        #以url中图片的名字命名
        self.file_name = self.url.split("/")[-1]
    
    def download_img(self):
        #下载图片
        response = requests.get(self.url)

        if response.status_code == 200:
            with open(self.download_folder + self.file_name, "wb") as f:
                f.write(response.content)
        else:
            print("下载失败")

    #从提示词中返回[颜色，朝向，目标物]的列表prompt_list    
    @staticmethod
    def get_prompt_list(prompt):
        #颜色
        color = ["红色", "绿色", "黄色", "蓝色", "灰色"]
        # 三维物体
        three = ["圆柱", "圆锥", "球", "立方体"]
        #大小写字母及数字
        letter_number = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

        prompt_list = []
        #添加颜色
        for c in color:
            if c in prompt:
                prompt_list.append(c)
                break
        else:
            prompt_list.append(None)
        
        #添加朝向
        if "侧向" in prompt:
            prompt_list.append("侧向")
        elif "正向" in prompt:
            prompt_list.append("正向")
        else:
            prompt_list.append(None)
        
        #添加目标物
        for l in letter_number:
            if l in prompt:
                if "大写" in prompt:     #处理大小写
                    l = l.upper()
                elif "小写" in prompt:
                    l = l.lower()
                prompt_list.append(l)
                return prompt_list 
        for t in three:
            if t in prompt:
                prompt_list.append(t)
                return prompt_list
        else:
            prompt_list.append(None)
            return prompt_list
    
    #查找prompt对应的结果
    @staticmethod
    def search_prompt(target, result_list):
        #一个信息不全的target，匹配多个result
        best_idx = 0
        idx = 0
        for result in result_list: #result为tuple(result, x, y)
            result = result[0]
            if target[2] == result[2]: #物体一致
                if target[0] == result[0] or target[1] == result[1]: #颜色或朝向不会同时出现，如果其中一个匹配，则可以确定参照物物体
                    return idx
                elif target[0] == None and result[0] == None:        #如果只有物体一个特征，则先存下来，其他情况说明特征不匹配
                    best_idx = idx
            idx += 1
        return best_idx   #返回匹配结果在result_list中的序号
    
    #查找target对应的结果
    @staticmethod
    def search_target(target, result_list):
        idx = 0
        best_idx = 0
        for result in result_list:
            result = result[0]
            match = 0 #特征匹配数
            if target[2] == result[2]:
                match += 1
                if target[1] == result[1]:
                    match += 1
                if target[0] == result[0]:
                    match += 1
                if match == 3:
                    return idx
                elif match == 2:
                    best_idx = idx
            idx += 1
        return best_idx
                
    '''
    三种类型提示词
    请点击[目标]
    请点击[参照物]朝向一样的[目标]
    请点击[参照物]颜色一样的[目标]
    '''
    #查找目标，返回最终匹配目标的中心点坐标
    def search(self):
        self.download_img()
        # list中每个元素为tuple (result, x, y) 其中result格式为[颜色，朝向，物体]
        result_list = YOLO_Predict(f"{self.download_folder}/{self.file_name}").predict()
        print(f"预测结果：{result_list}")
        
        #去掉提示中“请点击”三个字
        print(f"提示词：{self.tips}")
        tips = self.tips[3:] 
        #处理提示词，获得搜索目标
        if "朝向一样的" in tips:
            prompt, target = tips.split("朝向一样的")[0], tips.split("朝向一样的")[1] #提示词和目标
            prompt, target = self.get_prompt_list(prompt), self.get_prompt_list(target)
            print(f"提示词特征：{prompt}, 目标特征：{target}")
            print(f"查找提示词：{prompt}")

            match_prompt = result_list[self.search_prompt(prompt, result_list)][0]
            print(f"查找到提示词匹配的结果：{match_prompt}")

            target[1] = match_prompt[1]  #朝向一致

        elif "颜色一样的" in tips:
            prompt, target = tips.split("颜色一样的")[0], tips.split("颜色一样的")[1]
            prompt, target = self.get_prompt_list(prompt), self.get_prompt_list(target)
            print(f"提示词特征：{prompt}, 目标特征：{target}")
            print(f"查找提示词：{prompt}")
            match_prompt = result_list[self.search_prompt(prompt, result_list)][0]
            print(f"查找到提示词匹配的结果：{match_prompt}")

            target[0] = match_prompt[0]  #颜色一致
        else:
            prompt, target = None, self.get_prompt_list(tips)
            print(f"提示词特征：{prompt}, 目标特征：{target}")

        print(f"查找目标：{target}")
        match_target = result_list[self.search_target(target, result_list)]
        print(f"查找到目标：{match_target})")
        return (match_target[1], match_target[2]) #返回目标的中心点坐标

class Main():
    def __init__(self):
        #初始化
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.driver.set_window_size(1366,768)
        self.driver.get("https://dun.163.com/trial/space-inference")

        #切换至嵌入式验证码页面
        WebDriverWait(self.driver, timeout=10).until(lambda d: d.find_element(By.XPATH,"/html/body/main/div[1]/div/div[2]/div[2]/ul/li[2]")).click()
    
    def getUrl(self):
        #等待div加载完成
        self.driver.implicitly_wait(10)      
        Div = self.driver.find_element(By.XPATH,"/html/body/main/div[1]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[2]/div[3]/div")
        
        #等待验证码加载完成
        WebDriverWait(self.driver, timeout=10).until_not(EC.text_to_be_present_in_element((By.XPATH,"/html/body/main/div[1]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[2]/div[3]/div/div/div[2]/div[3]/div/span[2]"),"加载中"))
        TipElement = Div.find_element(By.XPATH,"//div/div[2]/div[3]/div/span[2]")
        
        #调整窗口位置，使验证码可以被看见，由于使用ActionChains时会自动使节点可见，这里弃用
        # self.driver.execute_script("arguments[0].scrollIntoView(false);",TipElement)  #不知道具体滚动高度
        # self.driver.execute_script("window.scrollTo(0,500);")

        #获取提示词和图片链接
        Tips = TipElement.text
        ImageElement = Div.find_element(By.XPATH,"//div/div[1]/div/div[1]/img[1]")
        Url = ImageElement.get_attribute("src")
        print(Tips, Url)
        
        # 推理
        XOffset, YOffset = Verification(Url, Tips).search()

        #点击图片左上角坐标加XOffset,YOffset的坐标
        ActionChains(self.driver).move_to_element_with_offset(ImageElement,XOffset,YOffset).click().perform()

        time.sleep(3)
        #如果点对了，则tips变为 验证成功
        #如果点错了 变为 验证失败，请重试 并自动刷新 这里print出来的会是下一个tips
        Tips = Div.find_element(By.XPATH,"//div/div[2]/div[3]/div/span[2]").text
        print(Tips)
        time.sleep(3)

    def main(self):
        self.getUrl()

if __name__ == "__main__":
    #Main().main()
    Verification("https://necaptcha.nosdn.127.net/f0dfcef80d3e4e57908bd33b60bb6465.jpg","请点击侧向的大写C").search()