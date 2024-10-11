from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromiumService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from Verify import Identify_gap
from DownloadImg import Download
from yidun_verify.main import Verification

import re
import time
                             
class PassWord:
    def __init__(self, Key):
        self.Key = Key

    def GetPassWord(self, Raw_Password): #密文转原密码
        Key = self.Key
        Real_PassWord = ""
        for a in Raw_Password:
            Real_PassWord += chr(ord(a) - Key)
        return Real_PassWord

    def GetRawPassWord(self, Real_Password): #原密码转密文
        Key = self.Key
        Raw_PassWord = ""
        for a in Real_Password:
            Raw_PassWord += chr(ord(a) + Key)
        return Raw_PassWord

class AutoPlay(PassWord):
    def __init__(self):
        #登录信息 对password进行加密
        self.Login_UserName = "13827520017"
        self.Login_PassWord_Fake = r"\t~ft<9snrjs"   #密文
        self.Key = 5

        self.ControlsBar = None #储存节点

        #继承PassWord类
        super(AutoPlay, self).__init__(self.Key)
        #获取密码
        self.RealPassWord = self.GetPassWord(self.Login_PassWord_Fake)

    def GetRealPassword(self):
        return self.RealPassWord

    def InitDevice(self):
        #初始化驱动
        self.driver = webdriver.Chrome(service=ChromiumService(r'.\driver\chromedriver.exe'))
        return 0
    
    def CloseDialog(self):
        #检查弹窗是否出现
        try:
            BreakPointDialog = WebDriverWait(self.driver, timeout=5).until(lambda d: d.find_element(By.XPATH,'//*[@id="playTopic-dialog"]/div'))
        # except NoSuchElementException:
        except:
            print("无弹窗")
            return -1
        #寻找选项列表
        # time.sleep(0.5)
        OptionList = BreakPointDialog.find_element(By.CLASS_NAME,"topic-list")
        OptionList = OptionList.find_element(By.TAG_NAME,"li")
        OptionList.find_element(By.TAG_NAME,("use")).click() #点击第一个选项
        
        # #遍历点击所有选项
        # OptionList = OptionList.find_elements(By.TAG_NAME,"li") 
        # for Option in OptionList:
        #     Option.find_element(By.TAG_NAME,("use")).click()

        #弹窗关闭按钮
        # BreakPointDialog.find_element(By.XPATH,"//div[1]/button/i").click() #报错element not interactable
        self.driver.find_element(By.XPATH,"/html/body/div[1]/div/div[2]/div[1]/div[2]/div[1]/div/div[1]/button/i").click()
        print("弹窗关闭完成")
        return 0
        
    def Login(self):
        driver = self.driver
        #隐式等待时间
        driver.implicitly_wait(10)    
        #加载登陆页面
        driver.get("https://passport.zhihuishu.com/login?service=https://onlineservice-api.zhihuishu.com/gateway/f/v1/login/gologin#signin")

        #输入登录信息并登录，然后手动完成验证登录
        Login_Element = driver.find_element(By.XPATH,"/html/body/div[8]/div/form/div[1]/ul[1]")
        Login_Element.find_element(By.XPATH,"//*[@id='lUsername']").send_keys(self.Login_UserName)
        Login_Element.find_element(By.XPATH,"//*[@id='lPassword']").send_keys(self.RealPassWord)
        # driver.find_element(By.XPATH,"/html/body/div[6]/div/form/div[1]/span").click()
 
        driver.find_element(By.XPATH,"/html/body/div[8]/div/form/div[1]/span").click()
        return 0

    def EnterCourse(self):
        driver = self.driver
        #显式等待课程列表加载完成
        ClassList = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.XPATH,"/html/body/div[1]/section/div[2]/section[2]/section/div/div/div/div[2]/div[1]/div[2]/ul[1]"))
        ClassList = ClassList.find_element(By.XPATH,"..") 
        CourseNames = ClassList.find_elements(By.CLASS_NAME,"courseName")
        for Course in CourseNames:
            if Course.text == "电力电子技术（广东工业大学）":
                Course.click()
                print(f"进入课程：{Course.text}")

        #关闭学前必读
        try:
            WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.XPATH,"/html/body/div[1]/div/div[6]/div[2]/div[1]/i")).click()
        # except ElementClickInterceptedException:
        except:
            pass
        print("学前必读关闭完成")
        return 0
    
    def DisplayControlsBar(self):
        #修改ControlsBar的style中display:none为display:block
        script = '''var divset=document.getElementsByClassName("controlsBar");
        	        for (var i = 0; i<divset.length;i++) {
        	 	        divset[i].style.display="block";
        	 	    };'''
        self.driver.execute_script(script)
        return 0

    #易盾验证码判断与识别
    def YidunVerify(self):
        try:
            imgElement = self.driver.find_element(By.CSS_SELECTOR, ".yidun_bg-img")
            imgText = self.driver.find_element(By.CSS_SELECTOR, ".yidun_tips__content").text
            print("检测到易盾验证码存在")
        except:
            print("未检测到易盾验证码存在")
            return 0
        imgSrc = imgElement.get_attribute("src")

        print(imgSrc, imgText)
        #验证码识别
        XOffset, YOffset = Verification(imgSrc, imgText).search()
        #点击图片左上角坐标加XOffset,YOffset的坐标
        ActionChains(self.driver).move_to_element_with_offset(imgElement,XOffset,YOffset).click().perform()
        print("易盾验证码点击完毕")
        return 1

    def Play(self):
        #如果有弹窗就关闭
        self.CloseDialog()

        #定位视频播放控制区
        self.DisplayControlsBar()
        self.ControlsBar = WebDriverWait(self.driver, timeout=10).until(lambda d: d.find_element(By.XPATH,"//*[@id='vjs_container']/div[10]"))
        while self.ControlsBar.find_element(By.CLASS_NAME,"duration").text == "":
            self.ControlsBar = WebDriverWait(self.driver, timeout=10).until(lambda d: d.find_element(By.XPATH,"//*[@id='vjs_container']/div[10]"))

        #如果视频没有播放完成
        #获取视频总长度
        duration = self.ControlsBar.find_element(By.CLASS_NAME,"duration").text
        duration = int(duration[-2:]) + int(duration[-5:-3])*60
        # print(f"视频长度：{duration}")

        #获取现在播放时间
        NowPlayTime = self.ControlsBar.find_element(By.CLASS_NAME,"currentTime").text
        NowPlayTime = int(NowPlayTime[-2:]) + int(NowPlayTime[-5:-3])*60
        # print(f"视频进度：{NowPlayTime}")

        #获取断点百分比
        VideoBreakPoint = self.driver.find_element(By.XPATH,"/html/body/div[1]/div/div[2]/div[1]/div[3]/ul/li").get_attribute("style")
        #正则表达式处理字符串 返回视频断点表示的时间百分比(小数形式)
        BPLocation = float("0." + re.search("\d+", VideoBreakPoint).group())
        #断点所在的秒数
        BPLocation = int(f"{(duration*BPLocation):.0f}")
        # print(f"BPlocation:{BPLocation}")

        #显示定位视频播放按钮并点击播放视频
        # self.DisplayControlsBar()
        self.ControlsBar.find_element(By.ID,"playButton").click()
        print("播放视频成功")

        #如果视频未完成播放，先判断duration和断点时间的位置
        #如果断点未到，延时等待关闭弹窗
        if NowPlayTime <= BPLocation:
            #延时到断点
            WaitTime = BPLocation - NowPlayTime + 5
            print(f"延时：{WaitTime}s后至断点")
            time.sleep(WaitTime) #留多5s
            self.CloseDialog()
            #弹窗关闭后重新播放视频
            self.DisplayControlsBar()
            self.ControlsBar.find_element(By.ID,"playButton").click()
            #等待视频播放完
            WaitTime = duration - BPLocation + 5
            print(f"延时:{WaitTime}s后播放完成")
            time.sleep(WaitTime)
        #如果已经过了断点
        else:
            WaitTime = duration - NowPlayTime + 5
            print(f"延时:{WaitTime}s后播放完成")
            time.sleep(WaitTime)
        
        #播放下一个视频前确认是否有易盾验证码窗口
        IsYidunVerify = self.YidunVerify()
        if IsYidunVerify == 1:
            print("验证码识别后重新延时")
            time.sleep(WaitTime)

        #播放下一个视频
        self.DisplayControlsBar()
        self.ControlsBar.find_element(By.ID,"nextBtn").click()
        print("播放下一个视频")
        return 0
    
    #输入滑块节点
    def Drag(self, Xoffset, SliderElement):
        ActionChains(self.driver).click_and_hold(on_element=SliderElement).perform()
        ActionChains(self.driver).move_by_offset(Xoffset, 0).perform()
        ActionChains(self.driver).pause(0.5).release().perform()

    def LoginIdentify(self):
        BgPath = "./images/BgImg.jpg"
        JigSawImgPath = "./images/JigsawImg.jpg"

        time.sleep(3)
        print("验证码识别中")

        try:
            BgImgElement = self.driver.find_element(By.CSS_SELECTOR, ".yidun_bg-img")
        except:
            print("验证码寻找失败，请手动验证")
            return -1
        
        BgImgSrc = BgImgElement.get_attribute("src")
        JigSawImgSrc = self.driver.find_element(By.CSS_SELECTOR,".yidun_jigsaw").get_attribute("src")

        Download(BgImgSrc, BgPath)
        Download(JigSawImgSrc, JigSawImgPath)

        #偏移量和图片原始尺寸
        Xoffset, RegionWidth = Identify_gap(BgPath, JigSawImgPath)
        #这里不知道为什么差了10点坐标，需要补上
        Xoffset = Xoffset* (BgImgElement.size['width']/RegionWidth) + 10

        #滑块
        SliderElement = self.driver.find_element(By.CSS_SELECTOR, ".yidun_slide_indicator")
        self.Drag(Xoffset, SliderElement)
        print("验证码点击完成")

    def Main(self):
        self.InitDevice()
        self.Login() #登录
        self.LoginIdentify()
        self.EnterCourse() #进入课程
        time.sleep(10)
        self.YidunVerify()
        while True:
            self.Play() #播放视频

if __name__ == "__main__":
    AutoPlay().Main()
