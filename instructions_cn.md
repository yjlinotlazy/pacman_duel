# pacman_duel 使用说明

## 依赖包

- Python 3.12+
- `PySide6`
- 如果要跑测试，还需要 `pytest`

示例安装：

```bash
pip install PySide6 pytest
```

## 启动命令

在仓库根目录运行：

```bash
python src/app.py
```

也可以用模块方式：

```bash
python -m src.app
```

## 菜单说明

游戏运行时，顶部配置面板会一直显示，不需要返回主菜单。

- `Board`：选择内置棋盘
- `Pacman`：选择人工控制或 Pacman 随机 AI
- `Slime AI`：选择史莱姆算法
- `Helper AI`：选择 helper 算法
- `Enemy speed scaling`：选择固定减速或 `Adaptive`

按钮：

- `Start Match`：按当前设置开始一局
- `Replay Current Config`：按相同设置立即重开
- `Stop Match`：停止当前对局，但保留顶部配置面板
- `Quit App`：退出程序

游戏内控制：

- 方向键：控制 Pacman
- `r`：按当前配置重开
- `q` 或 `Esc`：停止当前对局
