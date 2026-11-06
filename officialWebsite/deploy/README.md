# 官网 VPS 部署

正式地址：<https://revenge-web.gaocc.cc/>

本轮发布复用用户指定 VPS 上已有的 Debian 13、Nginx、Certbot 和续期定时器。Cloudflare 仅新增 `revenge-web` 的 A 记录，指向 `198.44.112.174`，已开启 Cloudflare 代理与静态资源缓存、TTL Auto；其他解析和全区 SSL 配置保持。

## 发布结构

- 站点配置：`/etc/nginx/sites-available/revenge-web`，经 `sites-enabled/revenge-web` 加载。
- 公共配置：`/etc/nginx/snippets/revenge-web-common.conf`。
- 当前目录：`/srv/www/revenge-web/current`，指向 `releases/<版本号>`。
- 发布校验与配置备份：`/srv/www/revenge-web/backups/`。
- 证书：`/etc/letsencrypt/live/revenge-web.gaocc.cc/`，由 Certbot 的 webroot 方式管理。
- 验证目录：`/var/www/letsencrypt/.well-known/acme-challenge/`。HTTP 80 保留此路径，其余流量跳转 HTTPS。
- 现有 `certbot.timer` 自动续期；现有 deploy hook 在成功续期后检查并重载 Nginx。
- 日志：`/var/log/nginx/revenge-web.access.log`、`/var/log/nginx/revenge-web.error.log`。

## 更新

1. 在官网目录运行 `npm run check` 与 `npm run optimize`。
2. 运行 `python3 deploy/package.py`，得到仅包含公开文件的发布包和 SHA-256 报告。
3. 用用户授权的 SSH 方式上传新包，解压到新的 `releases/<版本号>`，运行包内 `sha256sum -c SHA256SUMS`。
4. 将校验清单移到站点根目录之外，设置目录755、文件644。
5. 保留旧 `current` 指向，再通过临时符号链接和 `mv -T` 原子切换版本。
6. 如修改配置，先执行 `nginx -t`，通过后再 `systemctl reload nginx`。
7. 检查 HTTPS 首页、三语模块、图片与视频 Range 响应；失败时将 `current` 切回先前版本。

## 验证范围

已检查 49 个公开资源的状态和大小、服务器文件 SHA-256、HTTPS 跳转、gzip、视频 Range 分段、内部制作目录不可访问。开启代理后从 VPS 验证 Cloudflare 首页200、视频206与缓存命中，并在 Chrome 实际打开首页和播放实机视频。未改动全区现有 Full 加密模式或其他域名解析。

本机默认 Python urllib 请求被 Cloudflare 以1010拒绝；正常 Chrome 和 VPS 的公网请求通过，保留现有浏览器完整性检查。

本仓库不保存 VPS 密码、SSH 私钥或证书私钥。此次 SSH 助手直接读取用户指定登录文件，没有把密码写入命令参数、部署包或检查记录。

包中只包含 HTML、CSS、JavaScript、robots、sitemap、图片、视频与文字 gzip 副本。制作源图、Godot脚本、报告、部署脚本及 Git 信息均不进入公开目录。

此次部署报告：`../reports/deployment-20261028.json`。公网资源检查：`../reports/public-deployment-checks.json`。

## 2026-11-02 · MAP 内容更新

发布版本 `20261102-110932`，上一个版本 `20261028-221138` 保留。新增三语 MAP 介绍、5种状态、10张PC截图与点击播放的引擎演示。未调整Nginx、Cloudflare或TLS配置。服务器65个文件校验通过；公网15个更新资源与本地SHA-256一致，视频Range返回206并命中缓存，浏览器完整播放6.4秒。

发布记录：`../reports/deployment-20261102.json`；公网检查：`../reports/public-map-checks-20261102.json`；浏览器记录：`../reports/map-feature-browser-20261102.json`。回滚前核对current，再将其原子切回旧版本；之前的指向记录在 `/srv/www/revenge-web/backups/20261102-110932-previous.txt`。

### 同日第二次发布 · 20261102-112101

修正弓箭命中截图至第24帧，并将6.4秒演示入口前置到MAP技能选项之前。新图片使用独立资源名，HTML、CSS、脚本均更新版本参数。默认不加载/播放视频，点击才进入播放器。服务器65文件校验通过，公网6个重点资源与本地一致，视频Range返回206并命中缓存。上一版本 `20261102-110932` 保留。报告：`../reports/deployment-20261102b.json`、`../reports/public-map-fix-20261102b.json`。

## 2026-11-04 · 男女主必杀演出

版本 `20261104-113043` 已上线；上一版本 `20261102-112101` 保留。新增 `#critical-strikes` 三语介绍、四段PC引擎演示与八张无损截图，点击才播放。77个服务器文件校验通过，公网16个更新资源SHA-256与本地一致，4段视频均返回206并命中缓存；本地4段、线上2段完整播放通过。

未调整Nginx、DNS和TLS配置。部署记录：`../reports/deployment-20261104.json`；公网检查：`../reports/critical-public-20261104.json`；浏览器检查：`../reports/critical-browser-20261104.json`、`../reports/critical-online-20261104.json`。回滚指向记录：`/srv/www/revenge-web/backups/20261104-113043-previous.txt`。
