# Citation Tracker 📊

自动追踪 Google Scholar 论文引用量的工具。每天自动更新，生成可视化图表。

## 特性

- ✅ 自动抓取 Google Scholar 引用数据
- ✅ 每日自动更新
- ✅ 可视化每篇论文的引用趋势
- ✅ 支持暗黑模式
- ✅ 完全免费，基于 GitHub Pages

## 快速开始

### 1. Fork 这个仓库

点击右上角的 **Fork** 按钮。

### 2. 修改配置

打开 `config.py` 文件，修改 `SCHOLAR_URL` 为你的 Google Scholar 主页链接：

```python
SCHOLAR_URL = "https://scholar.google.com/citations?user=你的ID"
```

### 3. 启用 GitHub Pages

1. 进入仓库 **Settings**
2. 左侧菜单找到 **Pages**
3. Source 选择 **Deploy from a branch**
4. Branch 选择 **main**，文件夹选择 **/ (root)**
5. 点击 **Save**

### 4. 手动触发一次

1. 进入 **Actions** 页面
2. 点击 **Daily Citation Update**
3. 点击 **Run workflow** -> **Run workflow**

### 5. 查看结果

访问 `https://你的用户名.github.io/citation-tracker/`

## 配置说明

| 配置项 | 说明 |
|--------|------|
| `SCHOLAR_URL` | 你的 Google Scholar 主页链接 |

## 如何获取 Google Scholar 链接

1. 打开 [Google Scholar](https://scholar.google.com/)
2. 搜索你的名字
3. 点击你的个人主页
4. 复制浏览器地址栏的链接，类似：
   `https://scholar.google.com/citations?user=XXXXX`

## 常见问题

**Q: 页面显示 "Failed" 怎么办？**

A: 检查 `config.py` 中的链接是否正确，以及 GitHub Actions 日志是否有错误。

**Q: 如何手动更新数据？**

A: 进入 Actions 页面，点击 "Run workflow" 即可。

---

Made with ❤️ for researchers
