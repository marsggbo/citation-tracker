# Citation Tracker 📊

基于 [MyPaperTrend](https://github.com/marsggbo/MyPaperTrend) 浏览器扩展同步数据的 Google Scholar 引用趋势公开看板，部署在 GitHub Pages 上可直接外网访问。

## 数据流说明

1. **采集与同步**：浏览器安装 [MyPaperTrend](https://github.com/marsggbo/MyPaperTrend) 插件并开启 GitHub 云同步，直接在已登录的 Google Scholar 页面无感采集完整引用、h-index、i10-index，自动写入公开数据仓库 [`mypapertrend-data`](https://github.com/marsggbo/mypapertrend-data)（Schema v2：`citations-<scholar_id>.json`）。
2. **网页直读展示**：本仓库的 `index.html` 在浏览器端直接拉取 `mypapertrend-data` 的最新 JSON（主源 `raw.githubusercontent.com`，自动降级 `cdn.jsdelivr.net`），无需服务端爬虫或 ScraperAPI Key。
3. **多学者切换**：支持通过 URL 参数查看任意已同步的学者，例如：
   - 默认：`https://marsggbo.github.io/citation-tracker/`
   - 指定学者：`https://marsggbo.github.io/citation-tracker/?user=LYNKm_8AAAAJ`

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

Last updated: Sun Apr  5 15:00:56 +08 2026
