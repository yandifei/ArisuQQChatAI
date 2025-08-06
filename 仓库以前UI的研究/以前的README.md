# PyQt6无边框
***这是是适用所有的系统，但是在左上角和左边上边的拖拽是存在小问题的，2025.2.25我找到了利用winapi解决这个问题，有空再写一篇文章吧（win系统下完美解决去标题栏的问题）***
PyQt6自定义标题栏，拖拽、双击放大和复原、边缘拉伸、圆角、窗口贴边功能
使用的是PyQt6最新版，Python是3.9版本（源码能用就行，版本没必要遵守）
里面有开发文档，有自己的撰写思路
希望对方拿到就能直接用
源码里面90%的代码都有我的中文注释，几乎每行代码都有注释
frameless_window.py这个文件直接打开，拖到最底层代码，把“./边框重写.ui”修改为你自己的ui文件就可以了，当然，你可以把ui文件转为py文件调用也完全没问题。如：
```python
Free_my_WW_app = QApplication(sys.argv)  # 管理控制事件流和设置
Free_my_WW = WinInit("./边框重写.pyi")  # 创建实例对象
Free_my_WW.show()  # 展示窗口(在未初始化 GUI 前调用 show()	窗口可能无法正确渲染)
sys.exit(Free_my_WW_app.exec())  # 安全退出界面任务
```
这个py文件目前有2个需要手动调用的方法而已，一个是让你的ui界面一直置顶，另一个是去掉背景
这里要说明的是，ui界面开发时必须要有一个打底的控件，因为圆角边框就必须把最开始的背景去掉，如：Qwidget
打底的界面要开启鼠标跟踪（mouseTracking），这个在qtdesigner属性那一栏
这里面有我写一些包对游戏脚本开发很有帮助

Qtdesigner如果设置了最右上角有UI按钮（其他控件没测）的话，即使边缘缩放打开了也无效
最右上角如果有控件请填写大小，不然光标会是拉伸的光标（难看）

***
# 界面展示
![初始界面](https://github.com/yandifei/GUI_Designer-Qt6-/blob/main/UI%E5%9B%BE%E7%89%87/%E5%B1%95%E7%A4%BA%E5%9B%BE%E7%89%87.png?raw=true)
![图片展示](https://github.com/yandifei/GUI_Designer-Qt6-/blob/main/UI%E5%9B%BE%E7%89%87/%E5%B1%95%E7%A4%BA%E5%9B%BE%E7%89%871.png?raw=true)
![图片展示](https://github.com/yandifei/GUI_Designer-Qt6-/blob/main/UI%E5%9B%BE%E7%89%87/%E5%B1%95%E7%A4%BA%E5%9B%BE%E7%89%872.png?raw=true)
![图片展示](https://github.com/yandifei/GUI_Designer-Qt6-/blob/main/UI%E5%9B%BE%E7%89%87/%E5%B1%95%E7%A4%BA%E5%9B%BE%E7%89%873.png?raw=true)
![图片展示](https://github.com/yandifei/GUI_Designer-Qt6-/blob/main/UI%E5%9B%BE%E7%89%87/%E5%B1%95%E7%A4%BA%E5%9B%BE%E7%89%874.png?raw=true)
![图片展示](https://github.com/yandifei/GUI_Designer-Qt6-/blob/main/UI%E5%9B%BE%E7%89%87/%E5%B1%95%E7%A4%BA%E5%9B%BE%E7%89%875.png?raw=true)
![图片展示](https://github.com/yandifei/GUI_Designer-Qt6-/blob/main/UI%E5%9B%BE%E7%89%87/%E5%B1%95%E7%A4%BA%E5%9B%BE%E7%89%876.png?raw=true)
![图片展示](https://github.com/yandifei/GUI_Designer-Qt6-/blob/main/UI%E5%9B%BE%E7%89%87/%E5%B1%95%E7%A4%BA%E5%9B%BE%E7%89%877.png?raw=true)


## 通过继承实现(限windows系统)
使用别人的人库
```python
from qframelesswindow import FramelessWindow
```
保留了原生窗口拖拽拉伸和窗口贴边布局功能。
![图片展示](https://github.com/yandifei/GUI_Designer-Qt6/blob/7100d92b771949332d06be0d4abc863dcceae9f2/UI%E5%9B%BE%E7%89%87/%E7%BB%A7%E6%89%BF%E5%AE%9E%E7%8E%B01.png)

![图片展示](https://github.com/yandifei/GUI_Designer-Qt6/blob/7100d92b771949332d06be0d4abc863dcceae9f2/UI%E5%9B%BE%E7%89%87/%E7%BB%A7%E6%89%BF%E5%AE%9E%E7%8E%B02.png)

![图片展示](https://github.com/yandifei/GUI_Designer-Qt6/blob/7100d92b771949332d06be0d4abc863dcceae9f2/UI%E5%9B%BE%E7%89%87/%E7%BB%A7%E6%89%BF%E5%AE%9E%E7%8E%B03.png)