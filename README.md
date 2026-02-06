# MRobot

更加高效快捷的机器人开发工具，诞生于 Robocon 和 Robomaster，但绝不仅限于此。

<div align="center">
  <img src="assets\logo\MRobot.png" height="80" alt="MRobot Logo">
  <p>
    <img src="https://img.shields.io/github/license/goldenfishs/MRobot.svg" alt="License">
    <img src="https://img.shields.io/github/repo-size/goldenfishs/MRobot.svg" alt="Repo Size">
    <img src="https://img.shields.io/github/last-commit/goldenfishs/MRobot.svg" alt="Last Commit">
    <img src="https://img.shields.io/badge/language-c/python-F34B7D.svg" alt="Language">
  </p>
</div>

---

## 引言

提起嵌入式开发，绝大多数人对每次繁琐的配置，以及查阅各种文档来写东西感到非常枯燥和浪费使时间，对于小形形目创建优雅的架构又比较费事，那么我们有没有办法快速完成基础环境的搭建后直接开始写逻辑代码呢？

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
pyinstaller MRobot.py --onefile --windowed --add-data "assets/logo;assets/logo" --add-data "app;app" --add-data "app/tools;app/tools"
```