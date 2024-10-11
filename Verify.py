import cv2

def Identify_gap(bg,tp):
    '''
    bg: 背景图片
    tp: 缺口图片
    out:输出图片
    '''
    # 读取背景图片和缺口图片
    bg_img = cv2.imread(bg) # 背景图片
    tp_img = cv2.imread(tp) # 缺口图片

    bg_width = bg_img.shape[1]
    
    # 识别图片边缘
    bg_edge = cv2.Canny(bg_img, 100, 200)
    tp_edge = cv2.Canny(tp_img, 100, 200)
    
    # 转换图片格式
    bg_pic = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
    tp_pic = cv2.cvtColor(tp_edge, cv2.COLOR_GRAY2RGB)
    
    # 缺口匹配
    res = cv2.matchTemplate(bg_pic, tp_pic, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res) # 寻找最优匹配
    
    # 绘制方框
    tl = max_loc # 左上角点的坐标

    #这四行注释掉
    # th, tw = tp_pic.shape[:2] 
    # br = (tl[0]+tw,tl[1]+th) # 右下角点的坐标
    # cv2.rectangle(bg_img, tl, br, (0, 0, 255), 2) # 绘制矩形
    #cv2.imwrite(out, bg_img) # 保存在本地
    
    # 返回缺口的X坐标和图片原始尺寸
    return tl[0], bg_width

if __name__ == '__main__':
    bg = r"images/BgImg.jpg"
    tp = r"images/JigsawImg.jpg"
    out = "./images/201.jpg"
    print(Identify_gap(bg, tp))