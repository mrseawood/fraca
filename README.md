# 面部及肩膀裁剪工具

这是一个基于Python开发的图形界面工具，用于自动检测图片中的人脸，并智能裁剪出头部和肩膀区域，适用于人物肖像处理。

## 功能特点

- **自动人脸检测**：使用dlib库的人脸检测器自动识别图片中的人脸
- **智能裁剪**：根据面部特征和肩膀位置，智能裁剪出合适的头肩区域
- **批量处理**：支持批量处理整个文件夹中的图片
- **进度显示**：实时显示处理进度和日志信息
- **处理记录**：自动生成处理记录，记录成功和失败的图片信息
- **中文路径支持**：针对中文路径问题进行了特殊处理，提高兼容性
- **依赖自检**：自动检查并提示安装所需的依赖库

## 系统要求

- Windows操作系统
- Python 3.6+
- 必要的依赖库（见下方安装说明）

## 安装说明

### 1. 安装依赖库

本工具依赖以下Python库：

```
opencv-python
mediapipe
numpy
dlib
```

您可以通过以下命令安装这些依赖：

```
pip install -r requirements.txt
```

**注意**：dlib库的安装可能需要额外步骤：

- 安装Visual Studio Build Tools (包含C++编译器)：
  https://visualstudio.microsoft.com/visual-cpp-build-tools/

- 安装CMake：
  https://cmake.org/download/

- 确保上述工具安装完成后，使用以下命令安装dlib：
  ```
  pip install dlib
  ```

- 或者，您可以下载预编译的dlib wheel文件：
  https://github.com/z-mahmud22/Dlib_Windows_Python/releases

### 2. 下载人脸关键点模型文件

本工具需要dlib的人脸关键点模型文件才能正常工作：

1. 从官方下载地址获取模型文件：
   http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

2. 下载后解压，将`shape_predictor_68_face_landmarks.dat`文件放在程序同一目录下。

## 使用方法

1. 运行程序：
   ```
   python 面部及肩膀裁剪_GUI.py
   ```

2. 在程序界面中：
   - 点击"浏览..."选择包含图片的输入文件夹
   - 选择输出文件夹（默认为输入文件夹下的cropped_faces子文件夹）
   - 如果模型文件未自动检测到，点击"选择模型文件"手动选择
   - 点击"开始处理