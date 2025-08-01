# MRobot

更加高效快捷的 STM32 开发架构，诞生于 Robocon 和 Robomaster，但绝不仅限于此。

<div align="center">
  <img src="./img/MRobot.png" height="100" alt="MRobot Logo">
  <p>是时候使用更简洁的方式开发单片机了</p>
  <p>
    <!-- <img src="https://img.shields.io/github/license/xrobot-org/XRobot.svg" alt="License">
    <img src="https://img.shields.io/github/repo-size/xrobot-org/XRobot.svg" alt="Repo Size">
    <img src="https://img.shields.io/github/last-commit/xrobot-org/XRobot.svg" alt="Last Commit">
    <img src="https://img.shields.io/badge/language-c/c++-F34B7D.svg" alt="Language"> -->
  </p>
</div>

---

## 引言

提起嵌入式开发，绝大多数人对每次繁琐的配置，以及查阅各种文档来写东西感到非常枯燥和浪费使时间，对于小形形目创建优雅的架构又比较费事，那么我们哟u没有办法快速完成基础环境的搭建后直接开始写逻辑代码呢？

这就是**MRobot**。



---

## 获取源代码

（此处可补充获取代码的具体方法）

---

## 主要特色

（此处可补充项目的主要特色）

---

## 组成

<div align="center">
  <img src="./image/嵌入式程序层次图.png" alt="嵌入式程序层次图">
</div>

- `src/bsp`
- `src/component`
- `src/device`
- `src/module`
- `src/task`

---

## 应用案例

> **Robomaster**

- 全向轮步兵
- 英雄
- 哨兵

---

## 机器人展示

`以上机器人均使用 MRobot 搭建`

---

## 硬件支持

（此处可补充支持的硬件列表）

---

## 图片展示


## 相关依赖

（此处可补充项目依赖的具体内容）

---

## 构建 exe

使用以下命令构建可执行文件：

```bash
pyinstaller --onefile --windowed 
pyinstaller MR_Toolbox.py --onefile --noconsole --icon=img\M.ico --add-data "mr_tool_img\MRobot.png;mr_tool_img"

pyinstaller MR_Tool.py --onefile --noconsole --icon=img\M.ico --add-data "mr_tool_img\MRobot.png;mr_tool_img" --add-data "src;src" --add-data "User;User"

pyinstaller --noconfirm --onefile --windowed ^
  --add-data "User_code;User_code" ^
  --add-data "img;img" ^
  --icon "img\M.ico" ^
  MRobot.py


pyinstaller --noconfirm --onefile --windowed --add-data "img;img" --add-data "User_code;User_code" --add-data "mech_lib;mech_lib" --icon=img/MRobot.ico MRobot.py

python3 -m PyInstaller --noconfirm --onefile --windowed \
  --add-data "img:img" \
  --add-data "User_code:User_code" \
  --add-data "mech_lib:mech_lib" \
  --icon=img/MRobot.ico \
  MRobot.py

  
python3 -m PyInstaller --windowed --name MRobot \
  --add-data "img:MRobot.app/Contents/Resources/img" \
  --add-data "User_code:MRobot.app/Contents/Resources/User_code" \
  --add-data "mech_lib:MRobot.app/Contents/Resources/mech_lib" \
  MRobot.py



pyinstaller --noconfirm --onefile --windowed --add-data "img;img" --add-data "User_code;User_code" --icon=img/M.ico MRobot.py


pyinstaller MRobot.py

pyinstaller --noconfirm --onefile --windowed --icon=img/M.ico --add-data "img;img" --add-data "User_code;User_code" --add-data "mech_lib;mech_lib" MRobot.py


pyinstaller --onefile --windowed --icon=assets/logo/M.ico --add-data "assets/logo:assets/logo" --add-data "assets/User_code:assets/User_code" --add-data "assets/mech_lib:assets/mech_lib" --collect-all pandas MRobot.py

pyinstaller --onefile --windowed --icon=assets/logo/M.ico --add-data "assets/logo:assets/logo" --add-data "assets/User_code:assets/User_code" --add-data "assets/mech_lib:assets/mech_lib" MRobot.py

python3 -m pyinstaller MRobot.py --onefile --windowed --add-data "assets:assets" --add-data "app:app" --add-data "app/tools:app/tools"

python -m pyinstaller MRobot.py --onefile --windowed --add-data "assets;assets" --add-data "app;app" --add-data "app/tools;app/tools"

/Users/lvzucheng/Library/Python/3.9/bin/pyinstaller MRobot.py --onefile --windowed --add-data "assets:assets" --add-data "app:app" --add-data "app/tools:app/tools"

pyinstaller MRobot.py --onefile --windowed --add-data "assets;assets" --add-data "app;app" --add-data "app/tools;app/tools"