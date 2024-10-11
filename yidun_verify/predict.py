from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
import cv2
import os
import onnxruntime
from PIL import Image
import io
import numpy as np

class ColorClassify(object):
    def __init__(self, color_model_path):
        self.color_list = ["蓝色", "灰色", "绿色", "红色", "黄色"]
        if not os.path.exists(color_model_path):
            raise FileNotFoundError(f"Error! 模型路径无效: '{color_model_path}'")
        self._session = onnxruntime.InferenceSession(color_model_path)

    @staticmethod
    def softmax(x):
        """np实现torch.softmax"""
        e_x = np.exp(x - np.max(x))
        return e_x / np.sum(e_x)

    @staticmethod
    def read_img(image):
        """
        转换图片格式、形状（1,3,244,244）
        注意! 不能直接使用np.array来转换Image图片! 否则输出结果不正确
        """
        if isinstance(image, np.ndarray):
            img = image
        elif isinstance(image, bytes):
            img = cv2.imdecode(np.array(bytearray(image), dtype='uint8'), cv2.IMREAD_COLOR)
        elif isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            img = cv2.imdecode(np.array(bytearray(buf.getvalue()), dtype='uint8'), cv2.IMREAD_COLOR)
        elif isinstance(image, str):
            img = cv2.imread(image)
        else:
            raise ValueError(f"Error! 不支持的图片格式: {type(image)}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (224, 224)).astype(np.float32) / 255
        img = np.expand_dims(np.transpose(img, (2, 0, 1)), axis=0)
        return img

    def predict(self, image):
        img = self.read_img(image)
        result = self._session.run(None, {"input": img})
        output = self.softmax(result[0][0])
        # 最大值（置信度）
        # predict_cla = max(output)
        # 最大值索引
        index = np.argmax(output)
        return self.color_list[index]

class YOLO_Predict():
    def __init__(self, img_path):
        self.img_path = img_path
        self.color_onnx_path = "yidun_verify/models/color_best.onnx"
        self.yolo_onnx_path = "yidun_verify/models/best.onnx"
        
        self.Color_Classify = ColorClassify(self.color_onnx_path)
        self.final_result_list = []

    def predict(self):
        #加载onnx模型
        onnx_model = YOLO(self.yolo_onnx_path)
        names = onnx_model.names #存储分类的字典

        #预测结果
        results = onnx_model(self.img_path, imgsz=320)
        im0 = cv2.imread(self.img_path)
        
        #yolo模型预测结果转列表
        boxes = results[0].boxes.xyxy.cpu().tolist()
        clss = results[0].boxes.cls.cpu().tolist()
        # annotator = Annotator(im0, line_width=2, example=names) # useless
         
        idx = 0
        if boxes is not None:
            for box, cls in zip(boxes, clss):
                # annotator.box_label(box, color=colors(int(cls), True), label=names[int(cls)])
                #裁剪图片为每个预测结果
                x1, x2 = int(box[0]), int(box[2])
                y1, y2 = int(box[1]), int(box[3])
                crop_obj = im0[y1:y2, x1:x2]
                # print(x1,x2,y1,y2)

                #获取颜色分类结果
                color_result = self.Color_Classify.predict(crop_obj)
                yolo_result = names[int(cls)]
                # print(yolo_result,color_result)

                #将结果合在一起
                result = []
                result.append(color_result)
                result.append(yolo_result.split("_")[1])
                result.append(yolo_result.split("_")[0])
                #中心点坐标
                x = x1 + int((x2-x1)/2)
                y = y1 + int((y2-y1)/2)

                idx += 1
                self.final_result_list.append((result, x, y))
        return self.final_result_list

if __name__ == "__main__":
    img_path = "1.jpg"
    print(YOLO_Predict(img_path).predict())