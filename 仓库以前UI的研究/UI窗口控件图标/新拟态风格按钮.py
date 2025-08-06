import sys
from PyQt6.QtCore import Qt, QRectF, QRect, QSize
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap, QTransform, QIcon, QPen, QPainterPath
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsEffect, QGraphicsBlurEffect, QApplication, QWidget, QPushButton, QGraphicsPathItem, QStyleOptionButton, QStyle


class Shadow(QGraphicsEffect):
    def __init__(self):
        super().__init__()
        self.adjust=7

    def boundingRectFor(self, rect: QRectF) ->QRectF:
        adjust=self.adjust #adjust从0开始，每加1,pixmap尺寸增加3
        return rect.adjusted(-adjust, -adjust, adjust, adjust)

    def draw(self, painter: QPainter):
        mode = QGraphicsEffect.PixmapPadMode.PadToEffectiveBoundingRect  # 获取源图像和位置
        # pixmap的尺寸是按钮尺寸的1.5倍+adjust*3
        pixmap, offset = self.sourcePixmap(Qt.CoordinateSystem.DeviceCoordinates, mode=mode)
        if pixmap.isNull():
            return
        restore_transform = painter.worldTransform()  # 保存并重置坐标系
        painter.setWorldTransform(QTransform())
        shadow1 = self.create_shadow(pixmap, offset=11, color=QColor(180, 180, 180))
        # 生成第一个阴影
        shadow2 = self.create_shadow(pixmap, offset=4, color=QColor(255, 255, 255))
        # 生成第二个阴影
        painter.drawImage(offset, shadow1)
        # 绘制右下角黑色阴影
        painter.drawImage(offset, shadow2)  # 绘制左上角白色阴影
        painter.drawPixmap(offset, pixmap)  # 绘制原始图像
        painter.setWorldTransform(restore_transform)  # 恢复坐标系

    def create_shadow(self, pixmap: QPixmap, offset, color: QColor) -> QImage:
        img_size = pixmap.size()  # 创建基础图像
        shadow = QImage(img_size, QImage.Format.Format_ARGB32_Premultiplied)
        # QImage:Format_ARGB32_Premultiplied 是QImage类中定义的一种图像格式
        shadow.setDevicePixelRatio(pixmap.devicePixelRatio())
        # 设备像素比(DevicePixel Ratio，简称DPR）是用于描述屏幕物理像素与逻辑像素之间的比例关系
        shadow.fill(Qt.GlobalColor.transparent)  # 将阴影填充为完全透明
        scene = QGraphicsScene()
        path = QPainterPath()  # 创建 QPainterPath 对象
        width = int((pixmap.width() - self.adjust * 3) / 1.5) - 4  # 定义矩形区域
        height = int((pixmap.height() - self.adjust * 3) / 1.5)-4
        path.addRoundedRect(QRectF(offset, offset, width, height), 10, 10)
        # 添加圆角矩形到路径中
        rounded_item = QGraphicsPathItem(path)  # 创建QGraphicsPathItem,并传入路径
        rounded_item.setPen(QPen(Qt.GlobalColor.transparent))
        # 设置边框（画笔)
        rounded_item.setBrush(color)
        # 设置填充色(画刷)
        effect = QGraphicsBlurEffect()  # 创建QGraphicsBlurEffect对象
        effect.setBlurRadius(10)  # 设置模糊半径
        # 接着
        rounded_item.setGraphicsEffect(effect)
        scene.addItem(rounded_item)
        scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())  # 设置场景尺寸
        try:
            with QPainter(shadow) as p:
                view = QGraphicsView()
                view.resize(pixmap.width(),pixmap.height()) # 设置视图大小与目标pixmap一致
                view.move(0, 0)
                view.setRenderHints(
                    QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
                    # 设置渲染质量：抗锯齿+平滑像素变换
                )
                view.setScene(scene)  # 关联要渲染的场景
                view.render(
                    p,
                    QRectF(0, 0, pixmap.width(), pixmap.height()),
                    QRect(0, 0, pixmap.width(), pixmap.height())
                )  # 关键渲染操作：将场景内容绘制到QPainter的上下文中
        except Exception as e:
            print(e)
        return shadow

class SpacingButton(QPushButton):
    def __init__(self, parent, text: str, size: QSize, x: int, y: int, icon_path: str, icon_size: QSize):
        super().__init__(parent)
        self.text = text
        self.icon_size =icon_size
        self.resize(size)
        self.move(x, y)
        self.icon = QIcon(icon_path)
        self.style_option =QStyleOptionButton()
        self.icon_y = 0#初始缓存值
        self.show()

    def resizeEvent(self, event):
        self.icon_y=int(self.height()-self.icon_size.height()/2)#更新缓存的垂直位置
        super().resizeEvent(event)

    # 该类为间距按钮
    def paintEvent(self, event):
        painter = QPainter(self)
        self.style_option.initFrom(self)
        self.initStyleOption(self.style_option)
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, self.style_option, painter, self)
        self.icon.paint(painter, 15, self.icon_y, self.icon_size.width(), self.icon_size.height())
        painter.setPen(self.palette().color(self.foregroundRole()))
        text_rect = self.rect()
        text_rect.setLeft(self.icon_size.width() + 15)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(370, 120)
        self.setStyleSheet("background: #e9e9e9;")
        self.setWindowTitle("新拟态风格按钮")
        self.button1=SpacingButton(self,'开始测试',QSize(130,50),30,30,'B:/Qt界面模板开发/爱丽丝QQ聊天AI/resources/背景/光之剑.png',QSize(25,25))
        self.button1.setIconSize(QSize(25, 25))
        shadow = Shadow()
        self.button1.setGraphicsEffect(shadow)
        self.button1.setStyleSheet(
        "QPushButton{background: #e0e0e0; border: 0px; border-radius: 10px; font-size: 15px;}"
        "QPushButton:pressed{background: qlineargradient(x1:0, y1:0, x2:1, y2:1,stop: 0 #ccccc, stop: 0.5 #e0e0e0, stop: 0.8 #ffff, stop: 1 #ffff);"
        "border: 0px;"
        "border-radius: 10px;}"
        )

#程序入口
if __name__ == '__main__':
    app =QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())