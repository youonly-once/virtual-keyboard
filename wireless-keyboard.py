import cv2
import time
import cvzone
import numpy as np
from cvzone.HandTrackingModule import HandDetector
from pytesseract import pytesseract

"""
Created on : 2024-05-27
Author     : SXS
Email      : your.email@example.com
Version    : 1.0

"""


pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# 计算两点斜率
def calculate_slope(point1, point2):
    if point2[0] - point1[0] != 0:
        slope = (point2[1] - point1[1]) / (point2[0] - point1[0])
        return slope
    else:
        return None


# 计算点是否在一条直线
def check_collinearity(points):
    try:
        slope = calculate_slope(points[0], points[1])
        for i in range(1, np.array(points).shape[0] - 1):
            next_slope = calculate_slope(points[i], points[i + 1])
            if abs(next_slope - slope) > 1:
                return False
        return True
    # ...
    except TypeError:
        return False


class Anniu:
    def __init__(self, pos: tuple, label: str, height: int, width: int):
        self.pos = pos
        self.label = label
        self.height = height
        self.width = width

    def __lt__(self, other):
        return self.pos[1] < other.pos[1] if self.pos[0] - other.pos[0] < 5 else self.pos[0] < other.pos[0]


# 创建按钮

def draw_keyboard_single(imgNew, button: Anniu, text_pos: list, color, colorc):
    x, y = button.pos
    w, h = button.width, button.height
    cv2.rectangle(imgNew, (x, y), (x + w, y + h), color, cv2.FILLED)
    cvzone.cornerRect(imgNew, (x, y, w, h), 20, rt=0, colorC=colorc)
    cv2.putText(imgNew, button.label, (x + text_pos[0], y + text_pos[1]), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255),
                thickness=3)


# 绘制键盘
def draw_keyboard(img, buttonList):
    for button in buttonList:
        key = button.label
        if key.lower() != 'del' and key.lower() != 'enter' and key.lower() != 'sh' and key.lower() != 'ca' and key.lower() != 'ta':
            if caps:
                button.label = key.upper()
            else:
                button.label = key.lower()
        draw_keyboard_single(img, button, [22, 50], (0, 0, 0), (1, 255, 1))
    return img


caps = False


# 检测是否正在输入
def type_checker(raw_img, gray, img, text_finished, text_count, last_type_time, hand, detector):
    # 重新获取列表
    buttonList = []
    # 应用二值化（或者其他的阈值操作）
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # 寻找轮廓
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    index = 0
    # 绘制轮廓的边框
    for contour in (contours):
        # 获取每个轮廓的边界框
        x, y, w, h = cv2.boundingRect(contour)
        if (abs(w - h) > 10):
            continue
        if (w < 25 or w > 35):
            continue
        print(w)
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 绿色边框，线宽为2

        posi = int(index / 8)
        posj = int(index % 8)
        if posi>=3:
            print("out of range i")
            continue
        if posj>=8:
            print("out of range j")
            continue
        buttonList.append(Anniu((x, y), 'temp',h,w))
        index = index+1
    sorted(buttonList,reverse=True)
    global caps
    for button in buttonList:
        #获取每个按钮的坐标
        x, y = button.pos
        w, h = button.width, button.height
        for sub_hand in hand:
            #获取每只手食指与大拇指指尖坐标
            lm_list = sub_hand['lmList']
            x1, y1, z1 = lm_list[8]
            x2, y2, z2 = lm_list[4]
            #判断食指指尖是否在按钮坐标内，若是则颜色突出表示
            if x <= x1 <= x + w and y <= y1 <= y + h+25:
                cropped_image = raw_img[y:y + h, x:x + w]
                # 使用Pytesseract进行文字识别
                cong = r'--psm 10'
                text = pytesseract.image_to_string(cropped_image, config=cong)
                try:
                    if len(text) > 1:
                        text = text[0]
                except TypeError:
                    pass
                button.label = text

                # 输出识别的文字
                print(text)
                draw_keyboard_single(img, button, [22, 50], (0, 255, 0), (0, 175, 0))
                distance, _, img = detector.findDistance((x1, y1), (x2, y2), img)
                #设置敲击间隔
                timestamp_ms = int(time.time() * 1000)
                # 食指与大拇指尖间距小于20则认为在敲击当前字母
                if distance < 20 and timestamp_ms - last_type_time > 100:
                    last_type_time = timestamp_ms
                    draw_keyboard_single(img, button, [22, 65], (0, 255, 0), (0, 0, 255))

                    # TODO 实际控制键盘
                    if button.label.lower() == "ca":
                        caps = not caps
                    else:
                        text_finished += button.label
                        text_count += 1
    #敲击内容写到屏幕
    line_count = 61
    line_width = 1250
    lines = text_count // line_count
    line_height = 450 + lines * 25
    line_pos = (20, 400)
    #画一个矩形
    cv2.rectangle(img, line_pos, (line_width, line_height), (0, 0, 0), cv2.FILLED)
    for i in range(lines + 1):
        #指定位置写入敲击内容
        cv2.putText(img, text_finished[line_count * i:line_count * (i + 1)], (20, 425 + 25 * i), cv2.FONT_HERSHEY_PLAIN,
                    2, (255, 255, 255), thickness=2)
    return img, text_finished, text_count, last_type_time


def main():
    # 链接摄像头
    cap = cv2.VideoCapture(0)
    detector = HandDetector(staticMode=False,  # 视频流图像
                            maxHands=2,  # 最多检测2只手
                            detectionCon=0.8,  # 最小检测置信度
                            minTrackCon=0.5)  # 最小跟踪置信度

    text_count = 0
    text_finished = ""
    last_type_time = 0
    while True:
        ret, frame = cap.read()

        raw_img = frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        hand, frame = detector.findHands(frame, flipType=False)


        frame, text_finished, text_count, last_type_time = type_checker(raw_img,gray, frame, text_finished, text_count,
                                                                            last_type_time, hand,
                                                                            detector)
        # 显示一帧图像
        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
