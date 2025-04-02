import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import importlib.util
import webbrowser

# 全局变量
model_file_path = ""
model_status_var = None

# 检查并安装依赖库
def check_and_install_dependencies():
    # 使用after方法确保在主线程中显示消息框
    def show_message_in_main_thread(title, message, is_error=False):
        if is_error:
            root.after(0, lambda: messagebox.showerror(title, message))
        else:
            root.after(0, lambda: messagebox.showinfo(title, message))
    
    required_packages = {
        'opencv-python': 'cv2',
        'mediapipe': 'mediapipe',
        'numpy': 'numpy'
    }
    
    # dlib需要特殊处理
    special_packages = {
        'dlib': 'dlib'
    }
    
    missing_packages = []
    special_missing = []
    
    # 检查常规包
    for package, module in required_packages.items():
        if importlib.util.find_spec(module) is None:
            missing_packages.append(package)
    
    # 检查特殊包
    for package, module in special_packages.items():
        if importlib.util.find_spec(module) is None:
            special_missing.append(package)
    
    # 处理常规缺失的包
    if missing_packages:
        # 使用after方法确保在主线程中显示对话框
        result_var = tk.BooleanVar(value=False)
        
        def show_dialog():
            result = messagebox.askyesno(
                "缺少依赖库",
                f"检测到以下依赖库未安装: {', '.join(missing_packages)}\n\n是否自动安装这些库？"
            )
            result_var.set(result)
            if result:
                create_progress_window()
        
        root.after(0, show_dialog)
        
        # 等待对话框结果
        root.wait_variable(result_var)
        
        if result_var.get():
            return False  # 返回False表示依赖尚未准备好，安装过程将在另一个线程中进行
        else:
            root.after(0, lambda: messagebox.showwarning("警告", "缺少必要的依赖库，程序可能无法正常运行。"))
            return False
    elif special_missing:  # 只有特殊包缺失
        root.after(0, lambda: show_special_package_instructions(special_missing))
        return False
    else:
        # 所有依赖都已安装，导入它们
        try:
            global cv2, dlib, mp, np
            import cv2
            import dlib
            import mediapipe as mp
            import numpy as np
            return True  # 返回True表示依赖已准备好
        except ImportError as e:
            root.after(0, lambda: messagebox.showerror("导入错误", f"导入模块失败: {str(e)}"))
            return False

# 创建安装进度窗口
def create_progress_window():
    missing_packages = [package for package, module in {'opencv-python': 'cv2', 'mediapipe': 'mediapipe', 'numpy': 'numpy'}.items() 
                      if importlib.util.find_spec(module) is None]
    
    progress_window = tk.Toplevel()
    progress_window.title("安装依赖")
    progress_window.geometry("400x150")
    progress_window.resizable(False, False)
    progress_window.transient(root)  # 设置为主窗口的子窗口
    
    # 居中显示
    progress_window.update_idletasks()
    width = progress_window.winfo_width()
    height = progress_window.winfo_height()
    x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
    y = (progress_window.winfo_screenheight() // 2) - (height // 2)
    progress_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    label = tk.Label(progress_window, text="正在安装依赖库，请稍候...")
    label.pack(pady=10)
    
    progress = ttk.Progressbar(progress_window, orient="horizontal", length=350, mode="determinate")
    progress.pack(pady=10, padx=20)
    
    status_label = tk.Label(progress_window, text="")
    status_label.pack(pady=5)
    
    progress["maximum"] = len(missing_packages)
    progress["value"] = 0
    
    def install_packages():
        for i, package in enumerate(missing_packages):
            try:
                status_label.config(text=f"正在安装: {package}")
                progress_window.update()
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                progress["value"] = i + 1
                progress_window.update()
            except subprocess.CalledProcessError:
                root.after(0, lambda p=package: messagebox.showerror("安装失败", f"安装 {p} 失败，请手动安装。"))
        
        progress_window.destroy()
        
        # 检查是否还有特殊包需要安装
        special_missing = [package for package, module in {'dlib': 'dlib'}.items() 
                         if importlib.util.find_spec(module) is None]
        
        if special_missing:
            root.after(0, lambda: show_special_package_instructions(special_missing))
        else:
            root.after(0, lambda: messagebox.showinfo("安装完成", "所有依赖库已安装完成！"))
            # 重新导入必要的模块
            try:
                global cv2, mp, np
                import cv2
                import mediapipe as mp
                import numpy as np
                root.after(0, enable_buttons)
            except ImportError as e:
                root.after(0, lambda: messagebox.showerror("导入错误", f"导入模块失败: {str(e)}"))
                root.after(0, disable_buttons)
    
    threading.Thread(target=install_packages, daemon=True).start()

# 显示特殊包安装说明
def show_special_package_instructions(packages):
    if 'dlib' in packages:
        result = messagebox.askyesno(
            "需要手动安装dlib",
            "dlib库需要特殊安装步骤，因为它需要C++编译器和CMake。\n\n是否查看安装说明？"
        )
        if result:
            info_text = """dlib库安装说明：

1. 安装Visual Studio Build Tools (包含C++编译器):
   https://visualstudio.microsoft.com/visual-cpp-build-tools/

2. 安装CMake:
   https://cmake.org/download/

3. 确保上述工具安装完成后，使用以下命令安装dlib:
   pip install dlib

或者，您可以下载预编译的dlib wheel文件:
   https://github.com/Murtaza-Saeed/Dlib-Precompiled-Wheels-for-Python-on-Windows-x64-Easy-Installation

下载对应您Python版本的wheel文件，然后使用以下命令安装:
   pip install 下载的文件路径.whl

安装完成后，重新启动本程序。"""
            
            info_window = tk.Toplevel(root)
            info_window.title("dlib安装说明")
            info_window.geometry("600x400")
            info_window.resizable(False, False)
            info_window.transient(root)  # 设置为主窗口的子窗口
            
            # 居中显示
            info_window.update_idletasks()
            width = info_window.winfo_width()
            height = info_window.winfo_height()
            x = (info_window.winfo_screenwidth() // 2) - (width // 2)
            y = (info_window.winfo_screenheight() // 2) - (height // 2)
            info_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
            
            # 添加说明文本
            text_frame = tk.Frame(info_window)
            text_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            text = tk.Text(text_frame, wrap="word")
            text.pack(side="left", fill="both", expand=True)
            
            scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
            scrollbar.pack(side="right", fill="y")
            text.config(yscrollcommand=scrollbar.set)
            
            text.insert("1.0", info_text)
            text.config(state="disabled")
            
            # 添加按钮
            button_frame = tk.Frame(info_window)
            button_frame.pack(pady=10)
            
            tk.Button(
                button_frame,
                text="打开Visual Studio下载页",
                command=lambda: webbrowser.open("https://visualstudio.microsoft.com/visual-cpp-build-tools/")
            ).pack(side="left", padx=5)
            
            tk.Button(
                button_frame,
                text="打开CMake下载页",
                command=lambda: webbrowser.open("https://cmake.org/download/")
            ).pack(side="left", padx=5)
            
            tk.Button(
                button_frame,
                text="打开dlib预编译包",
                command=lambda: webbrowser.open("https://github.com/z-mahmud22/Dlib_Windows_Python/releases")
            ).pack(side="left", padx=5)
            
            tk.Button(
                button_frame,
                text="关闭",
                command=info_window.destroy
            ).pack(side="left", padx=5)

# 选择输入文件夹
def select_input_folder():
    folder_selected = filedialog.askdirectory(title="选择包含图片的文件夹")
    if folder_selected:
        input_folder_var.set(folder_selected)
        # 自动设置输出文件夹为输入文件夹下的cropped_faces子文件夹
        output_folder_var.set(os.path.join(folder_selected, "cropped_faces"))

# 选择输出文件夹
def select_output_folder():
    folder_selected = filedialog.askdirectory(title="选择输出文件夹")
    if folder_selected:
        output_folder_var.set(folder_selected)

# 处理图片的函数
def process_images():
    input_folder = input_folder_var.get()
    output_folder = output_folder_var.get()
    
    if not input_folder or not output_folder:
        messagebox.showwarning("警告", "请选择输入和输出文件夹！")
        return
    
    # 检查是否已安装所有必要的库
    try:
        import cv2
        import dlib
        import mediapipe as mp
        import numpy as np
    except ImportError as e:
        messagebox.showerror("缺少依赖", f"缺少必要的库: {str(e)}\n请先安装所有依赖库。")
        return
    
    # 禁用按钮，防止重复点击
    disable_buttons()
    
    # 创建并配置进度窗口
    progress_window = tk.Toplevel(root)
    progress_window.title("处理进度")
    progress_window.geometry("500x200")
    progress_window.resizable(False, False)
    progress_window.transient(root)  # 设置为主窗口的子窗口
    
    # 居中显示
    progress_window.update_idletasks()
    width = progress_window.winfo_width()
    height = progress_window.winfo_height()
    x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
    y = (progress_window.winfo_screenheight() // 2) - (height // 2)
    progress_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # 进度条和标签
    progress_label = tk.Label(progress_window, text="正在处理图片...")
    progress_label.pack(pady=10)
    
    progress = ttk.Progressbar(progress_window, orient="horizontal", length=450, mode="determinate")
    progress.pack(pady=10, padx=20)
    
    status_label = tk.Label(progress_window, text="准备中...")
    status_label.pack(pady=5)
    
    log_frame = tk.Frame(progress_window)
    log_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    log_text = tk.Text(log_frame, height=5, width=50, wrap="word")
    log_text.pack(side="left", fill="both", expand=True)
    
    scrollbar = ttk.Scrollbar(log_frame, command=log_text.yview)
    scrollbar.pack(side="right", fill="y")
    log_text.config(yscrollcommand=scrollbar.set)
    
    # 处理图片的线程函数
    def processing_thread():
        try:
            # 确保输出文件夹存在
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("错误", f"创建输出文件夹失败: {str(e)}\n可能是路径中包含中文字符导致的问题。")
                enable_buttons()
                return
            
            # 加载 Dlib 面部检测器 & 人脸关键点
            try:
                detector = dlib.get_frontal_face_detector()
                
                # 使用全局模型文件路径
                global model_file_path
                
                # 如果用户已经选择了模型文件，直接使用
                if model_file_path:
                    # 详细检查文件是否存在和可访问
                    try:
                        if os.path.exists(model_file_path) and os.path.isfile(model_file_path):
                            # 尝试打开文件以确认访问权限
                            with open(model_file_path, 'rb') as f:
                                # 只读取少量字节以验证文件可读
                                f.read(10)
                            predictor_path = model_file_path
                            found = True
                            log_text.insert(tk.END, f"✅ 使用用户选择的模型文件: {os.path.basename(predictor_path)}\n")
                            log_text.see(tk.END)
                            print(f"使用用户选择的模型文件: {predictor_path}")
                        else:
                            log_text.insert(tk.END, f"❌ 用户选择的模型文件不存在或不是文件: {model_file_path}\n")
                            log_text.see(tk.END)
                            print(f"用户选择的模型文件不存在或不是文件: {model_file_path}")
                            found = False
                    except Exception as e:
                        log_text.insert(tk.END, f"❌ 无法访问用户选择的模型文件: {str(e)}\n")
                        log_text.see(tk.END)
                        print(f"无法访问用户选择的模型文件: {str(e)}")
                        found = False
                else:
                    found = False
                
                # 如果没有找到用户选择的模型文件，尝试默认路径
                if not found:
                    log_text.insert(tk.END, "⚠️ 尝试查找默认模型文件...\n")
                    log_text.see(tk.END)
                    
                    # 获取当前脚本所在目录
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    predictor_path = os.path.join(script_dir, "shape_predictor_68_face_landmarks.dat")
                    
                    # 尝试多种可能的路径查找模型文件
                    possible_paths = [
                        predictor_path,  # 脚本目录中的路径
                        os.path.abspath("shape_predictor_68_face_landmarks.dat"),  # 当前工作目录的绝对路径
                        "shape_predictor_68_face_landmarks.dat",  # 相对路径
                        os.path.join(os.getcwd(), "shape_predictor_68_face_landmarks.dat"),  # 显式使用当前工作目录
                        os.path.join(".", "shape_predictor_68_face_landmarks.dat")  # 显式相对路径
                    ]
                    
                    # 检查所有可能的路径
                    for path in possible_paths:
                        try:
                            if os.path.exists(path) and os.path.isfile(path):
                                # 尝试打开文件以确认访问权限
                                with open(path, 'rb') as f:
                                    # 只读取少量字节以验证文件可读
                                    f.read(10)
                                predictor_path = path
                                found = True
                                log_text.insert(tk.END, f"✅ 成功找到默认模型文件: {os.path.basename(path)}\n")
                                log_text.see(tk.END)
                                print(f"成功找到默认模型文件: {predictor_path}")
                                break
                        except Exception as e:
                            print(f"尝试访问路径 {path} 失败: {str(e)}")
                
                # 打印文件路径信息以便调试
                if found:
                    print(f"尝试加载模型文件: {predictor_path}")
                    print(f"文件是否存在: {os.path.exists(predictor_path)}")
                
                if not found:
                    progress_window.destroy()
                    if model_file_path:  # 如果用户选择了模型但文件不存在或无法访问
                        messagebox.showerror("错误", f"无法加载选择的模型文件: {model_file_path}\n请确认文件存在、格式正确且有访问权限。")
                    else:
                        paths_tried = "\n".join([f"{i+1}. {p}" for i, p in enumerate(possible_paths)])
                        messagebox.showerror("错误", f"找不到人脸关键点模型文件。\n已尝试查找以下路径:\n{paths_tried}")
                    check_model_file()
                    enable_buttons()
                    return
                    
                # 尝试加载模型并提供详细的成功信息
                try:
                    # 获取文件大小和路径信息用于调试
                    file_size = os.path.getsize(predictor_path)
                    abs_path = os.path.abspath(predictor_path)
                    log_text.insert(tk.END, f"📂 模型文件信息:\n  路径: {predictor_path}\n  绝对路径: {abs_path}\n  文件大小: {file_size} 字节\n")
                    log_text.see(tk.END)
                    
                    # 处理可能的中文路径问题
                    try:
                        # 检查是否包含中文路径
                        has_chinese = False
                        for char in predictor_path:
                            if '\u4e00' <= char <= '\u9fff':
                                has_chinese = True
                                break
                        
                        if has_chinese:
                            log_text.insert(tk.END, f"⚠️ 检测到中文路径，尝试创建临时文件...\n")
                            log_text.see(tk.END)
                            
                            # 创建临时目录（如果不存在）
                            temp_dir = os.path.join(os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__))), 'face_crop_temp')
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            # 创建一个临时文件名（使用原文件名的哈希值）
                            import hashlib
                            file_hash = hashlib.md5(predictor_path.encode('utf-8')).hexdigest()
                            temp_file_path = os.path.join(temp_dir, f"model_{file_hash}.dat")
                            
                            # 复制文件到临时位置
                            import shutil
                            shutil.copy2(predictor_path, temp_file_path)
                            log_text.insert(tk.END, f"✅ 已创建临时文件: {temp_file_path}\n")
                            log_text.see(tk.END)
                            
                            # 使用临时文件路径加载模型
                            predictor = dlib.shape_predictor(temp_file_path)
                        else:
                            predictor = dlib.shape_predictor(predictor_path)
                    except UnicodeDecodeError:
                        # 尝试使用绝对路径和临时文件
                        log_text.insert(tk.END, f"⚠️ 检测到可能的中文路径问题，尝试使用临时文件...\n")
                        log_text.see(tk.END)
                        
                        try:
                            # 创建临时目录（如果不存在）
                            temp_dir = os.path.join(os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__))), 'face_crop_temp')
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            # 创建一个临时文件名（使用原文件名的哈希值）
                            import hashlib
                            file_hash = hashlib.md5(abs_path.encode('utf-8')).hexdigest()
                            temp_file_path = os.path.join(temp_dir, f"model_{file_hash}.dat")
                            
                            # 复制文件到临时位置
                            import shutil
                            shutil.copy2(abs_path, temp_file_path)
                            log_text.insert(tk.END, f"✅ 已创建临时文件: {temp_file_path}\n")
                            log_text.see(tk.END)
                            
                            # 使用临时文件路径加载模型
                            predictor = dlib.shape_predictor(temp_file_path)
                        except Exception as temp_error:
                            log_text.insert(tk.END, f"⚠️ 临时文件创建失败，尝试使用绝对路径...\n")
                            log_text.see(tk.END)
                            predictor = dlib.shape_predictor(abs_path)
                    
                    log_text.insert(tk.END, f"✅ 成功加载模型文件: {os.path.basename(predictor_path)}\n")
                    log_text.insert(tk.END, f"✅ 模型类型: shape_predictor, 68个面部关键点\n")
                    log_text.see(tk.END)
                    
                    # 更新全局模型状态
                    update_model_status(f"模型已加载: {os.path.basename(predictor_path)}")
                    
                    # 模型加载成功，但不显示提示窗口
                    if not hasattr(process_images, 'model_loaded_shown'):
                        # 使用一个标志来记录模型已加载
                        process_images.model_loaded_shown = True
                except UnicodeDecodeError as e:
                    log_text.insert(tk.END, f"❌ 模型加载失败: 路径中包含中文字符导致编码问题\n")
                    log_text.insert(tk.END, f"❌ 错误详情: {str(e)}\n")
                    log_text.see(tk.END)
                    progress_window.destroy()
                    messagebox.showerror("错误", f"模型加载失败: 路径中包含中文字符导致编码问题\n请将模型文件移动到不含中文的路径下，或重命名为英文路径。")
                    enable_buttons()
                    return
                except Exception as e:
                    log_text.insert(tk.END, f"❌ 模型加载失败: {str(e)}\n")
                    log_text.see(tk.END)
                    progress_window.destroy()
                    messagebox.showerror("错误", f"模型加载失败: {str(e)}\n请确保选择了正确的shape_predictor_68_face_landmarks.dat文件。")
                    enable_buttons()
                    return
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("错误", f"加载人脸检测模型失败: {str(e)}\n\n请确保shape_predictor_68_face_landmarks.dat文件在当前目录下。")
                enable_buttons()
                return
            
            # 初始化 MediaPipe Pose
            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # 获取所有图片文件
            try:
                image_files = [f for f in os.listdir(input_folder) 
                              if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"))]
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("错误", f"读取输入文件夹失败: {str(e)}\n可能是路径中包含中文字符导致的问题。")
                enable_buttons()
                return
            
            if not image_files:
                progress_window.destroy()
                messagebox.showinfo("提示", "所选文件夹中没有找到图片文件！")
                enable_buttons()
                return
            
            # 设置进度条最大值
            progress["maximum"] = len(image_files)
            progress["value"] = 0
            
            # 处理每张图片
            success_count = 0
            fail_count = 0
            
            # 创建处理记录列表
            processing_records = []
            
            for i, filename in enumerate(image_files):
                image_path = os.path.join(input_folder, filename)
                
                # 更新状态
                status_text = f"处理中: {i+1}/{len(image_files)} - {filename}"
                status_label.config(text=status_text)
                progress_window.update()
                
                try:
                    # 处理中文路径
                    image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if image is None:
                        log_message = f"❌ 无法读取: {filename}\n"
                        log_text.insert(tk.END, log_message)
                        log_text.see(tk.END)
                        fail_count += 1
                        continue

                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    faces = detector(gray)

                    if faces:
                        for face in faces:
                            landmarks = predictor(gray, face)
                            x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()

                            # 关键点获取优化
                            chin = landmarks.part(8)
                            forehead = landmarks.part(27)  # 眉间点
                            left_temple = landmarks.part(0)  # 左太阳穴
                            right_temple = landmarks.part(16) # 右太阳穴

                            # 计算头部顶点（头顶上方20%面部高度）
                            face_height = int(chin.y - forehead.y)
                            head_top = max(0, int(forehead.y - face_height * 1.2))  # 转换为整数

                            # 头部安全边界（左右各扩展15%）
                            face_width = x2 - x1
                            head_left = max(0, int(left_temple.x - face_width * 0.15))
                            head_right = min(image.shape[1], int(right_temple.x + face_width * 0.15))

                            # 身体检测
                            body_y = image.shape[0]  # 默认取图片底部
                            body_width = face_width * 2  # 默认身体宽度
                            results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                            if results.pose_landmarks:
                                landmarks_pose = results.pose_landmarks.landmark
                                left_shoulder = landmarks_pose[mp_pose.PoseLandmark.LEFT_SHOULDER]
                                right_shoulder = landmarks_pose[mp_pose.PoseLandmark.RIGHT_SHOULDER]

                                # 计算肩膀参数（添加int转换）
                                body_y = int(max(left_shoulder.y, right_shoulder.y) * image.shape[0])
                                shoulder_center = int((left_shoulder.x + right_shoulder.x)/2 * image.shape[1])
                                body_width = int(abs(left_shoulder.x - right_shoulder.x) * image.shape[1] * 1.5)

                            # 最终裁剪区域计算（强制整数转换）
                            final_y1 = int(max(0, head_top - face_height * 0.1))
                            final_y2 = int(min(image.shape[0], max(body_y, chin.y + face_height * 0.2)))
                            final_width = int(max(body_width, (head_right - head_left) * 1.2))
                            
                            # 中心点计算（确保整数运算）
                            head_center = int((head_left + head_right) // 2)
                            final_x1 = int(max(0, head_center - final_width//2))
                            final_x2 = int(min(image.shape[1], head_center + final_width//2))

                            # 动态调整宽度（添加int转换）
                            current_height = final_y2 - final_y1
                            ideal_width = int(current_height * 0.7)
                            if (final_x2 - final_x1) < ideal_width:
                                delta = ideal_width - (final_x2 - final_x1)
                                final_x1 = int(max(0, final_x1 - delta//2))
                                final_x2 = int(min(image.shape[1], final_x2 + delta//2))

                            # 进行裁剪
                            cropped = image[final_y1:final_y2, final_x1:final_x2]

                            # 结果校验
                            if cropped.shape[0] > 0 and cropped.shape[1] > 0:
                                try:
                                    # 使用os.path.join创建输出路径，确保路径分隔符正确
                                    output_path = os.path.join(output_folder, filename)
                                    # 保留原始文件扩展名
                                    file_ext = os.path.splitext(filename)[1].lower()
                                    # 如果是不支持的格式，默认使用jpg
                                    if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"]:
                                        file_ext = ".jpg"
                                    # 使用imencode和tofile处理中文路径
                                    cv2.imencode(file_ext, cropped)[1].tofile(output_path)
                                    log_message = f"✅ 裁剪并保存: {filename}\n"
                                    success_count += 1
                                    processing_records.append(f"[成功] {filename}")
                                except Exception as save_error:
                                    log_message = f"❌ 保存失败 {filename}: {str(save_error)}\n"
                                    fail_count += 1
                                    processing_records.append(f"[失败] {filename} - 保存失败: {str(save_error)}")
                                log_text.insert(tk.END, log_message)
                                log_text.see(tk.END)
                    else:
                        log_message = f"⚠️ 未检测到人脸: {filename}\n"
                        log_text.insert(tk.END, log_message)
                        log_text.see(tk.END)
                        fail_count += 1
                        processing_records.append(f"[失败] {filename} - 未检测到人脸")
                        
                except Exception as e:
                    log_message = f"❌ 处理失败 {filename}: {str(e)}\n"
                    log_text.insert(tk.END, log_message)
                    log_text.see(tk.END)
                    fail_count += 1
                    processing_records.append(f"[失败] {filename} - 处理失败: {str(e)}")
                
                # 更新进度条
                progress["value"] = i + 1
                progress_window.update()
            
            # 处理完成
            status_label.config(text=f"处理完成! 成功: {success_count}, 失败: {fail_count}")
            progress_label.config(text="所有图片处理完成！")
            
            # 导出处理记录到txt文件
            try:
                import datetime
                record_file_path = os.path.join(output_folder, "处理记录.txt")
                with open(record_file_path, "w", encoding="utf-8") as f:
                    f.write(f"处理时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"输入文件夹: {input_folder}\n")
                    f.write(f"输出文件夹: {output_folder}\n")
                    f.write(f"总计处理: {len(image_files)} 张图片\n")
                    f.write(f"成功: {success_count} 张\n")
                    f.write(f"失败: {fail_count} 张\n\n")
                    f.write("详细记录:\n")
                    for record in processing_records:
                        f.write(f"{record}\n")
                log_text.insert(tk.END, f"✅ 处理记录已保存至: 处理记录.txt\n")
                log_text.see(tk.END)
            except Exception as e:
                log_text.insert(tk.END, f"❌ 保存处理记录失败: {str(e)}\n")
                log_text.see(tk.END)
            
            # 添加完成按钮
            tk.Button(
                progress_window, 
                text="完成", 
                command=progress_window.destroy,
                width=10
            ).pack(pady=10)
            
            # 如果有成功处理的图片，提供打开输出文件夹的选项
            if success_count > 0:
                tk.Button(
                    progress_window,
                    text="打开输出文件夹",
                    command=lambda: open_folder_with_explorer(output_folder),
                    width=15
                ).pack(pady=5)
            
            enable_buttons()
            
        except Exception as e:
            messagebox.showerror("错误", f"处理过程中发生错误: {str(e)}")
            progress_window.destroy()
            enable_buttons()
    
    # 启动处理线程
    threading.Thread(target=processing_thread, daemon=True).start()

# 启用所有按钮
def enable_buttons():
    input_folder_button.config(state="normal")
    output_folder_button.config(state="normal")
    process_button.config(state="normal")

# 禁用所有按钮
def disable_buttons():
    input_folder_button.config(state="disabled")
    output_folder_button.config(state="disabled")
    process_button.config(state="disabled")

# 使用explorer打开文件夹（更好地支持中文路径）
def open_folder_with_explorer(folder_path):
    try:
        import subprocess
        # 使用subprocess调用explorer.exe打开文件夹，这样可以更好地处理中文路径
        subprocess.Popen(['explorer', folder_path])
    except Exception as e:
        messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")
        # 尝试使用os.startfile作为备选方案
        try:
            os.startfile(folder_path)
        except Exception as e2:
            messagebox.showerror("错误", f"备选方法也失败: {str(e2)}\n请手动打开文件夹: {folder_path}")

# 关于信息
def show_about():
    about_text = """面部及肩膀裁剪工具 v1.0

这是一个自动检测人脸并裁剪出头部和肩膀区域的工具。

使用方法：
1. 选择包含图片的文件夹
2. 选择输出文件夹（默认为输入文件夹下的cropped_faces子文件夹）
3. 点击"开始处理"按钮

注意：本工具需要shape_predictor_68_face_landmarks.dat文件才能正常工作。

© 2025 一模型Ai (https://jmlovestore.com) - 不会开发软件吗 🙂 Ai会哦"""
    
    about_window = tk.Toplevel(root)
    about_window.title("关于")
    about_window.geometry("400x300")
    about_window.resizable(False, False)
    about_window.transient(root)  # 设置为主窗口的子窗口
    
    # 居中显示
    about_window.update_idletasks()
    width = about_window.winfo_width()
    height = about_window.winfo_height()
    x = (about_window.winfo_screenwidth() // 2) - (width // 2)
    y = (about_window.winfo_screenheight() // 2) - (height // 2)
    about_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # 添加关于信息
    text = tk.Text(about_window, wrap="word", padx=10, pady=10)
    text.pack(fill="both", expand=True)
    text.insert("1.0", about_text)
    text.config(state="disabled")
    
    # 添加关闭按钮
    tk.Button(
        about_window,
        text="关闭",
        command=about_window.destroy,
        width=10
    ).pack(pady=10)

# 检查模型文件
def check_model_file():
    global model_file_path
    update_status("正在检查模型文件...")
    
    # 如果用户已经选择了模型文件，直接使用
    if model_file_path:
        try:
            if os.path.exists(model_file_path) and os.path.isfile(model_file_path):
                # 获取文件大小和路径信息用于调试
                file_size = os.path.getsize(model_file_path)
                abs_path = os.path.abspath(model_file_path)
                print(f"检查用户选择的模型文件: {model_file_path}")
                print(f"绝对路径: {abs_path}")
                print(f"文件大小: {file_size} 字节")
                
                # 尝试打开文件以确认访问权限
                with open(model_file_path, 'rb') as f:
                    # 只读取少量字节以验证文件可读
                    f.read(10)
                
                # 测试模型是否可以正确加载
                update_status("正在加载模型文件...")
                success, message = test_model_loading(model_file_path)
                if success:
                    print(f"使用用户选择的模型文件并成功加载: {model_file_path}")
                    update_model_status(f"模型已加载: {os.path.basename(model_file_path)}")
                    update_status("模型文件已加载，系统就绪")
                    return True
                else:
                    print(f"用户选择的模型文件无法加载: {message}")
                    update_model_status(f"模型加载失败: {message}", False)
                    update_status(f"模型加载失败: {message}")
            else:
                print(f"用户选择的模型文件不存在或不是文件: {model_file_path}")
                update_model_status("模型文件不存在", False)
                update_status("模型文件不存在，请选择有效的模型文件")
        except Exception as e:
            print(f"无法访问用户选择的模型文件: {str(e)}")
            update_model_status(f"无法访问模型文件: {str(e)}", False)
            update_status(f"无法访问模型文件: {str(e)}")
            # 重置模型文件路径，因为当前路径无效
            model_file_path = ""
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_file = os.path.join(script_dir, "shape_predictor_68_face_landmarks.dat")
    
    # 尝试多种可能的路径查找模型文件
    possible_paths = [
        model_file,  # 脚本目录中的路径
        os.path.abspath("shape_predictor_68_face_landmarks.dat"),  # 当前工作目录的绝对路径
        "shape_predictor_68_face_landmarks.dat",  # 相对路径
        os.path.join(os.getcwd(), "shape_predictor_68_face_landmarks.dat"),  # 显式使用当前工作目录
        os.path.join(".", "shape_predictor_68_face_landmarks.dat")  # 显式相对路径
    ]
    
    update_status("正在搜索模型文件...")
    # 检查所有可能的路径
    found = False
    for path in possible_paths:
        try:
            if os.path.exists(path) and os.path.isfile(path):
                # 获取文件大小和路径信息用于调试
                file_size = os.path.getsize(path)
                abs_path = os.path.abspath(path)
                print(f"找到可能的模型文件: {path}")
                print(f"绝对路径: {abs_path}")
                print(f"文件大小: {file_size} 字节")
                
                # 尝试打开文件以确认访问权限
                with open(path, 'rb') as f:
                    # 只读取少量字节以验证文件可读
                    f.read(10)
                
                # 测试模型是否可以正确加载
                update_status(f"正在尝试加载模型: {os.path.basename(path)}...")
                success, message = test_model_loading(path)
                if success:
                    model_file = path
                    model_file_path = path  # 保存找到的路径
                    found = True
                    print(f"成功找到模型文件并加载: {model_file}")
                    update_model_status(f"模型已加载: {os.path.basename(path)}")
                    update_status("模型文件加载成功，系统就绪")
                    break
                else:
                    print(f"找到模型文件但无法加载: {path}, 错误: {message}")
            else:
                print(f"路径不存在或不是文件: {path}")
        except Exception as e:
            print(f"尝试访问路径 {path} 失败: {str(e)}")
    
    # 打印调试信息
    if found:
        print(f"检查模型文件路径: {model_file}")
        print(f"文件是否存在: {os.path.exists(model_file) and os.path.isfile(model_file)}")
    else:
        print("未找到有效的模型文件")
        update_model_status("未找到有效的模型文件", False)
        update_status("未找到有效的模型文件，请手动选择")
    
    if not found:
        # 使用after方法确保messagebox在主线程中显示
        paths_tried = "\n".join([f"{i+1}. {p}" for i, p in enumerate(possible_paths)])
        print(f"尝试过的所有路径:\n{paths_tried}")
        root.after(0, lambda: show_model_download_info("shape_predictor_68_face_landmarks.dat"))
        return False
    return True

# 显示模型下载信息
def show_model_download_info(model_file):
    result = messagebox.askyesno(
        "缺少模型文件",
        f"未找到人脸关键点模型文件: {model_file}\n\n该文件对于人脸检测是必需的。\n\n是否查看下载说明？"
    )
    if result:
        download_info = """请从以下地址下载人脸关键点模型文件：

1. 官方下载地址：
   http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

2. 下载后解压，并将shape_predictor_68_face_landmarks.dat文件放在程序同一目录下。

注意：该文件大小约为100MB。"""
        
        info_window = tk.Toplevel(root)
        info_window.title("下载说明")
        info_window.geometry("500x300")
        info_window.resizable(False, False)
        info_window.transient(root)  # 设置为主窗口的子窗口
        
        # 居中显示
        info_window.update_idletasks()
        width = info_window.winfo_width()
        height = info_window.winfo_height()
        x = (info_window.winfo_screenwidth() // 2) - (width // 2)
        y = (info_window.winfo_screenheight() // 2) - (height // 2)
        info_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # 添加下载信息
        text_frame = tk.Frame(info_window)
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        text = tk.Text(text_frame, wrap="word")
        text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.config(yscrollcommand=scrollbar.set)
        
        text.insert("1.0", download_info)
        text.config(state="disabled")
        
        # 添加按钮
        button_frame = tk.Frame(info_window)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="打开下载页面",
            command=lambda: webbrowser.open("http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
        ).pack(side="left", padx=10)
        
        tk.Button(
            button_frame,
            text="关闭",
            command=info_window.destroy,
            width=10
        ).pack(side="left", padx=10)

# 全局变量，用于存储模型文件路径和状态
model_file_path = ""
model_status_var = None  # 将在主界面初始化时设置

# 测试模型文件是否可以正确加载
def test_model_loading(file_path):
    try:
        # 尝试加载模型文件
        import dlib
        # 处理中文路径问题
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        
        # 打印详细的文件信息以便调试
        file_size = os.path.getsize(file_path)
        print(f"尝试加载模型文件: {file_path}")
        print(f"文件大小: {file_size} 字节")
        
        # 使用绝对路径加载模型
        abs_path = os.path.abspath(file_path)
        
        # 检查是否包含中文路径
        has_chinese = False
        for char in abs_path:
            if '\u4e00' <= char <= '\u9fff':
                has_chinese = True
                break
        
        if has_chinese:
            # 对于中文路径，创建临时文件链接或复制
            try:
                # 创建临时目录（如果不存在）
                temp_dir = os.path.join(os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__))), 'face_crop_temp')
                os.makedirs(temp_dir, exist_ok=True)
                
                # 创建一个临时文件名（使用原文件名的哈希值）
                import hashlib
                file_hash = hashlib.md5(abs_path.encode('utf-8')).hexdigest()
                temp_file_path = os.path.join(temp_dir, f"model_{file_hash}.dat")
                
                # 复制文件到临时位置
                import shutil
                shutil.copy2(abs_path, temp_file_path)
                print(f"已创建临时文件: {temp_file_path}")
                
                # 使用临时文件路径加载模型
                predictor = dlib.shape_predictor(temp_file_path)
                return True, "模型加载成功！(通过临时文件)"
            except Exception as temp_error:
                print(f"创建临时文件失败: {str(temp_error)}")
                # 如果临时文件方法失败，尝试直接加载
                predictor = dlib.shape_predictor(abs_path)
                return True, "模型加载成功！"
        else:
            # 非中文路径直接加载
            predictor = dlib.shape_predictor(abs_path)
            return True, "模型加载成功！"
    except UnicodeDecodeError as ude:
        # 特别处理中文路径问题
        print(f"UnicodeDecodeError: {str(ude)}")
        try:
            # 尝试使用临时文件方法
            temp_dir = os.path.join(os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__))), 'face_crop_temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            import hashlib
            file_hash = hashlib.md5(file_path.encode('utf-8')).hexdigest()
            temp_file_path = os.path.join(temp_dir, f"model_{file_hash}.dat")
            
            import shutil
            shutil.copy2(file_path, temp_file_path)
            print(f"UnicodeDecodeError后创建临时文件: {temp_file_path}")
            
            predictor = dlib.shape_predictor(temp_file_path)
            return True, "模型加载成功！(通过临时文件)"
        except Exception as e:
            return False, f"模型文件路径包含中文字符，无法加载: {str(e)}"
    except Exception as e:
        return False, f"模型加载失败: {str(e)}"

# 更新模型状态显示
def update_model_status(status_text, is_success=True):
    global model_status_var
    if is_success:
        model_status_var.set(f"✅ {status_text}")
    else:
        model_status_var.set(f"❌ {status_text}")

# 选择模型文件
def select_model_file():
    global model_file_path
    update_status("正在选择模型文件...")
    file_selected = filedialog.askopenfilename(
        title="选择模型文件",
        filetypes=[("DAT文件", "*.dat"), ("所有文件", "*.*")]
    )
    if file_selected:
        # 验证文件是否存在且可访问
        try:
            if os.path.exists(file_selected) and os.path.isfile(file_selected):
                # 获取文件大小和路径信息用于调试
                file_size = os.path.getsize(file_selected)
                abs_path = os.path.abspath(file_selected)
                print(f"用户选择的模型文件: {file_selected}")
                print(f"绝对路径: {abs_path}")
                print(f"文件大小: {file_size} 字节")
                
                # 检查是否包含中文路径
                has_chinese = False
                for char in file_selected:
                    if '\u4e00' <= char <= '\u9fff':
                        has_chinese = True
                        break
                
                if has_chinese:
                    print("警告: 文件路径包含中文字符，可能导致加载问题")
                    update_status("警告: 文件路径包含中文字符")
                
                # 尝试打开文件以确认访问权限
                with open(file_selected, 'rb') as f:
                    # 只读取少量字节以验证文件可读
                    f.read(10)
                
                # 测试模型是否可以正确加载
                update_status("正在测试模型加载...")
                success, message = test_model_loading(file_selected)
                
                if success:
                    model_file_path = file_selected
                    # 不显示成功提示窗口，只在控制台打印信息和更新状态栏
                    print(f"用户选择的模型文件并成功加载: {model_file_path}")
                    update_model_status(f"模型已加载: {os.path.basename(model_file_path)}")
                    update_status("模型文件已加载，系统就绪")
                    return True
                else:
                    messagebox.showerror("错误", f"模型文件无法加载: {message}\n请确保选择了正确的shape_predictor_68_face_landmarks.dat文件。")
                    print(f"模型文件无法加载: {message}")
                    update_model_status(f"模型加载失败: {message}", False)
                    update_status(f"模型加载失败: {message}")
            else:
                messagebox.showerror("错误", "所选文件不存在或不是有效文件。")
                print(f"所选文件不存在或不是有效文件: {file_selected}")
                update_model_status("模型文件无效", False)
                update_status("所选文件不存在或无效")
        except UnicodeDecodeError as e:
            messagebox.showerror("错误", f"文件路径包含中文字符导致编码问题: {str(e)}\n请将文件移动到不含中文的路径下，或重命名为英文路径。")
            print(f"文件路径包含中文字符导致编码问题: {str(e)}")
            update_model_status("中文路径导致编码问题", False)
            update_status("中文路径导致编码问题")
        except Exception as e:
            messagebox.showerror("错误", f"无法访问所选文件: {str(e)}")
            print(f"无法访问所选文件: {str(e)}")
            update_model_status(f"无法访问模型文件: {str(e)}", False)
            update_status(f"无法访问模型文件: {str(e)}")
    else:
        update_status("已取消选择模型文件")
    return False

# 主程序
if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    root.title("面部及肩膀裁剪工具")
    root.geometry("600x400")
    root.resizable(False, False)
    
    # 居中显示
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # 创建样式
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10))
    style.configure("TLabel", font=("Arial", 10))
    style.configure("TFrame", padding=10)
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding="20 20 20 20")
    main_frame.pack(fill="both", expand=True)
    
    # 标题标签
    title_label = tk.Label(main_frame, text="面部及肩膀裁剪工具", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)
    
    # 说明标签
    description_label = tk.Label(
        main_frame, 
        text="此工具可以自动检测图片中的人脸，并裁剪出头部和肩膀区域。",
        wraplength=500,
        justify="center"
    )
    description_label.pack(pady=10)
    
    # 输入文件夹选择
    input_frame = ttk.Frame(main_frame)
    input_frame.pack(fill="x", pady=10)
    
    input_label = ttk.Label(input_frame, text="输入文件夹:")
    input_label.pack(side="left", padx=5)
    
    input_folder_var = tk.StringVar()
    input_entry = ttk.Entry(input_frame, textvariable=input_folder_var, width=50)
    input_entry.pack(side="left", padx=5, fill="x", expand=True)
    
    input_folder_button = ttk.Button(input_frame, text="浏览...", command=select_input_folder)
    input_folder_button.pack(side="left", padx=5)
    
    # 输出文件夹选择
    output_frame = ttk.Frame(main_frame)
    output_frame.pack(fill="x", pady=10)
    
    output_label = ttk.Label(output_frame, text="输出文件夹:")
    output_label.pack(side="left", padx=5)
    
    output_folder_var = tk.StringVar()
    output_entry = ttk.Entry(output_frame, textvariable=output_folder_var, width=50)
    output_entry.pack(side="left", padx=5, fill="x", expand=True)
    
    output_folder_button = ttk.Button(output_frame, text="浏览...", command=select_output_folder)
    output_folder_button.pack(side="left", padx=5)
    
    # 模型文件选择
    model_frame = ttk.Frame(main_frame)
    model_frame.pack(fill="x", pady=10)
    
    model_button = ttk.Button(
        model_frame,
        text="选择模型文件",
        command=select_model_file,
        width=15
    )
    model_button.pack(side="left", padx=10)
    
    model_label = ttk.Label(model_frame, text="可选：手动选择shape_predictor_68_face_landmarks.dat文件")
    model_label.pack(side="left", padx=5)
    
    # 模型状态显示
    model_status_frame = ttk.Frame(main_frame)
    model_status_frame.pack(fill="x", pady=5)
    
    # 使用全局变量，不需要再次声明
    model_status_var = tk.StringVar(value="⚠️ 模型状态未知")
    model_status_label = ttk.Label(model_status_frame, textvariable=model_status_var, font=("Arial", 10, "bold"))
    model_status_label.pack(side="left", padx=10)
    
    # 处理按钮
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=20)
    
    process_button = ttk.Button(
        button_frame, 
        text="开始处理", 
        command=process_images,
        width=15
    )
    process_button.pack(side="left", padx=10)
    
    about_button = ttk.Button(
        button_frame,
        text="关于",
        command=show_about,
        width=10
    )
    about_button.pack(side="left", padx=10)
    
    # 版权信息
    copyright_frame = ttk.Frame(root)
    copyright_frame.pack(side="bottom", fill="x")
    
    copyright_label = ttk.Label(copyright_frame, text="© 2025 一模型Ai (https://jmlovestore.com) - 不会开发软件吗 🙂 Ai会哦", anchor="center", font=("Arial", 9))
    copyright_label.pack(side="bottom", pady=3, fill="x")
    
    # 状态栏
    status_frame = ttk.Frame(root)
    status_frame.pack(side="bottom", fill="x")
    
    status_label = ttk.Label(status_frame, text="就绪", anchor="w")
    status_label.pack(side="left", padx=10, pady=5)
    
    # 状态更新函数
    def update_status(message):
        status_label.config(text=message)
        root.update_idletasks()
    
    # 初始化检查函数
    def initialize_app():
        try:
            update_status("正在检查依赖库...")
            if not check_and_install_dependencies():
                # 如果依赖库未准备好，禁用处理按钮
                disable_buttons()
                update_status("依赖库检查未通过，请安装所需依赖")
                update_model_status("依赖库未安装，无法检查模型", False)
            else:
                update_status("正在检查模型文件...")
                # 检查模型文件
                if check_model_file():
                    update_status("模型文件已加载，系统就绪")
                else:
                    update_status("模型文件检查未通过，请选择有效的模型文件")
                    # 模型状态已在check_model_file中更新
        except Exception as e:
            print(f"初始化过程中发生错误: {str(e)}")
            update_status(f"初始化错误: {str(e)}")
            update_model_status(f"初始化错误: {str(e)}", False)
            messagebox.showerror("初始化错误", f"程序初始化过程中发生错误:\n{str(e)}\n\n请尝试重新启动程序。")
            disable_buttons()
    
    # 在单独的线程中执行初始化检查
    threading.Thread(target=initialize_app, daemon=True).start()
    
    # 启动主循环
    root.mainloop()