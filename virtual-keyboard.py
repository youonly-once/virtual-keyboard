import cv2
import time
import cvzone
import numpy as np
from cvzone.HandTrackingModule import HandDetector

"""
Created on : 2024-05-27
Author     : SXS
Email      : your.email@example.com
Version    : 1.0

"""


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
def create_button():
    button_label = [
        ['Ta', "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "Back"],
        ['Ca', "K", "L", "M", "N", "O", "P", "Q", "R", "S", ";", "Del"],
        ['Sh', "T", "U", "V", "W", "X", "Y", "Z", ",", ".", "/", "Enter"]
    ]
    width_list = [[0 for _ in range(15)] for _ in range(4)]
    posx_list = [[0 for _ in range(15)] for _ in range(4)]
    button_list = []
    for i, row in enumerate(button_label):
        for j, label in enumerate(row):
            if len(label) >= 2:
                width = 50 * (len(label) // 4 + 2)
            else:
                width = 75
            if j == 0:
                x = 20
            else:
                x = (width_list[i][j - 1]) + posx_list[i][j - 1] + 21
            width_list[i][j] = width
            posx_list[i][j] = x
            button_list.append(Anniu((x, 100 * (i + 1)), label, 75, width))
    return button_list


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


def draw_result(img, text_finished, text_count):
    # 敲击内容写到屏幕
    line_count = 61
    line_width = 1250
    lines = text_count // line_count
    line_height = 450 + lines * 25
    line_pos = (20, 400)
    # 画一个矩形
    cv2.rectangle(img, line_pos, (line_width, line_height), (0, 0, 0), cv2.FILLED)
    for i in range(lines + 1):
        # 指定位置写入敲击内容
        cv2.putText(img, text_finished[line_count * i:line_count * (i + 1)], (20, 425 + 25 * i), cv2.FONT_HERSHEY_PLAIN,
                    2, (255, 255, 255), thickness=2)


# 检测是否正在输入
def type_checker(img, text_finished, text_count, last_type_time, button_list, hand, detector):
    global caps
    for button in button_list:
        # 获取每个按钮的坐标
        x, y = button.pos
        w, h = button.width, button.height
        for sub_hand in hand:
            # 获取每只手食指与大拇指指尖坐标
            lm_list = sub_hand['lmList']
            x1, y1, z1 = lm_list[8]
            x2, y2, z2 = lm_list[4]
            # 判断食指指尖是否在按钮坐标内，若是则颜色突出表示
            if x <= x1 <= x + w and y <= y1 <= y + h:
                draw_keyboard_single(img, button, [22, 50], (0, 255, 0), (0, 175, 0))
                distance, _, img = detector.findDistance((x1, y1), (x2, y2), img)
                # 设置敲击间隔
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
    draw_result(img, text_finished, text_count)
    return img, text_finished, text_count, last_type_time


# 手写字
def draw_line(img, points_list=None, point_i=None, hand=None, detector=None):
    lm_list = hand[0]['lmList']
    bbox = hand[0]['bbox']
    x1, y1, z1 = lm_list[8]

    x2, y2, z2 = lm_list[4]  # lmList[12]

    x3, y3, z3 = lm_list[19]
    x4, y4, z4 = lm_list[18]
    x5, y5, z5 = lm_list[17]

    # 定义四个点的坐标
    points = [[x5, y5], [x4, y4], [x3, y3]]
    new_points_list = []
    # 手掌为直线，擦除线段
    if check_collinearity(points):
        for sublist in points_list:
            new_sublist = []
            for p in sublist:
                if bbox[0] < p[0] < bbox[0] + bbox[2] and bbox[1] < p[1] < bbox[1] + bbox[3]:
                    pass
                else:
                    new_sublist.append(p)
            new_points_list.append(new_sublist)

        points_list = new_points_list
    # 添加点
    else:

        len, _, img = detector.findDistance((x1, y1), (x2, y2), img)
        # 判断四个点是否连接成直线
        is_collinear = len < 40
        if is_collinear:
            points_list[point_i].append([x1, y1])
        else:
            point_i = point_i + 1
            points_list.append([])
            points_list[point_i].append([x1, y1])
    # 绘制点
    for points in points_list:
        points = np.array(points)
        # 将多点坐标转换为OpenCV要求的格式
        points = points.reshape((-1, 1, 2))

        # 绘制多点线段
        color = (0, 0, 255)  # 线段颜色，BGR 格式
        thickness = 2  # 线段粗细
        is_closed = False  # 是否闭合多边形

        cv2.polylines(img, [points], is_closed, color, thickness)
    return img, points_list, point_i


def main():
    # 链接摄像头
    cap = cv2.VideoCapture(0)
    cap.set(3, 1920)
    cap.set(4, 1080)
    detector = HandDetector(staticMode=False,  # 视频流图像
                            maxHands=2,  # 最多检测2只手
                            detectionCon=0.8,  # 最小检测置信度
                            minTrackCon=0.5)  # 最小跟踪置信度

    text_count = 0
    text_finished = ""
    last_type_time = 0
    points_list = [[]]
    point_i = 0
    button_list = create_button()
    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        hand, frame = detector.findHands(frame, flipType=False)

        # 判断手的数量
        if hand:
            if len(hand) == 2:
                frame = draw_keyboard(frame, button_list)
                frame, text_finished, text_count, last_type_time = type_checker(frame, text_finished, text_count,
                                                                                last_type_time, button_list, hand,
                                                                                detector)
            elif len(hand) == 1:
                frame, points_list, point_i = draw_line(frame, points_list, point_i, hand, detector)
        # 显示一帧图像
        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
