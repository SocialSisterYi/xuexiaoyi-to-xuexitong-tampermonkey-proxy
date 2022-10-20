# 基于“学小易”搜题 API 的学习通答题/考试油猴脚本题库代理

本项目适用于与 TamperMonkey 用户脚本对接

解决公共题库失效或接口风控导致的无法搜题，同时解决学习通前端页面字体加密的问题

使用抓包和反编译取得“学小易” ~~客户端（已弃用）~~ 微信小程序的搜题接口，用于转发搜题请求返回脚本正确答案，从而代替公共题库接口

# 准备食材

- Python3.6+
- 任何基于 chrome/firefox 的浏览器
- TamperMonkey 插件
- TamperMonkey 学习通自动刷课用户脚本

# 处理食材

## 安装依赖

```bash
pip install -r requirement.txt
```

## 配置服务端（可选

修改`config.yaml`中的配置
 
 - host：服务端绑定地址
 - port：服务端接口
 - enable_cache：是否启用搜题缓存
 - xxy_open_id：“学小易 APP”微信小程序接口的 session（**请通过抓包提取请求头中的`wx-open-id`字段**

## 修改用户脚本

这里以用户脚本：[超星学习通网课助手|视频挂机考试答题|全网聚合题库每日自动更新适用于几乎所有专业科目|完全免费永久使用【网课通用版】](https://greasyfork.org/zh-CN/scripts/426360) 举例，其他类似脚本请参考下文自行修改

将该用户脚本中的**搜题API**改成你的服务端 host:port，同时注释掉原公共题库 API，这里用`192.168.1.3:88`举例

```javascript
var setting = {
    //tiku: 'http://api.muketool.com'
    tiku: '192.168.1.3:88/'
    ......
```

并把服务端 host 加入用户脚本的跨域白名单

```javascript
// @connect      api.muketool.com
// @connect      api2.muketool.com
// @connect      192.168.1.3
```

接着，需要破解字体加密（加密后的效果如下

![](http://i0.hdslb.com/bfs/album/063c3182c89dd22878bf783f71d9b08929b135f1.png)

需向脚本中添加以下两个函数

```javascript
// 拾取加密字体
function getSecFont() {
    return $("style[type='text/css']").text().match(/'(data:application\/font-ttf;.*?)'/)[1]
}

// 解密全部字体
function decryptAll() {
    let secFont = getSecFont(),
        encryptTexts = $('.TiMu').find('div.font-cxsecret,.font-cxsecret a');
    // 遍历加密字体项
   encryptTexts.each(function() {
       let dstText = $(this);
        GM_xmlhttpRequest({
            method: 'POST',
            url: `${setting.tiku}/decrypt`,
            headers: {
                'Content-type': 'application/json',
            },
            data: JSON.stringify({secFont: secFont, dstText: dstText.text().trim()}),
            responseType: 'json',
            onload: function (xhr) {
                 if (xhr.status == 200) {
                     dstText.text(xhr.response.srcText);
                     dstText.removeClass('font-cxsecret');
                 }
             }
         });
    });
}
```

并在合适的位置调用`decryptAll()`函数

```javascript
......
setting.lose = setting.num = 0;
setting.data = parent._data = [];
setting.over = '<button style="margin-right: 10px;">跳过此题</button>';
setting.curs = $('script:contains(courseName)', top.document).text().match(/courseName:\'(.+?)\'|$/)[1] || $('h1').text().trim() || '无';
setting.loop = setInterval(findAnswer, setting.time);
var tip = ({
    undefined: '任务点排队中', null: '等待切换中'
})[setting.tip];
tip && setting.div.children('div:eq(0)').data('html', tip).siblings('button:eq(0)').click();

decryptAll(); // 在这里添加
......
```

# 做菜

启动服务端

```bash
python3 app.py
```

服务端启动后将在指定 ip 上监听端口，这里为`192.168.1.3:88`

```
 * Serving Flask app 'app' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on all addresses.
   WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://192.168.1.3:88/ (Press CTRL+C to quit)
```

# 开吃

浏览器启动修改好的 TamperMonkey 用户脚本，进入学习通答题/考试页面，即可开始自动搜题

![](http://i0.hdslb.com/bfs/album/51e821730faff7acea76f1b6d43fbf1e139aa239.jpg)

# 饭后甜点（参考文献

[研究学习通答题字体加密的随笔](https://shakaianee.top/archives/558/)

[研究学习通答题字体加密的随笔（二）](https://shakaianee.top/archives/661/)

[\[Web逆向\] 关于超星学习通网页版字体加密分析](https://www.52pojie.cn/forum.php?mod=viewthread&tid=1631357)

# 技术资料-API接口

## 搜题

> http://127.0.0.1/v1/cx

*方法：POST*

请求体（application/x-www-form-urlencoded）：

```
question=目标题目
```

响应（application/json）：

```json
{
    "code": 1,      // 响应状态 1: 成功 -1: 失败
    "messsage": "", // 错误信息
    "data": "",     // 搜题结果
    "hit": true     // 是否命中题目缓存
}
```

## 解密

> http://127.0.0.1/decrypt

*方法：POST*

请求体（application/json）：

```json
{
    "secFont": "", // 密钥字体 base64
    "dstText": ""  // 目标密文本字符串
}
```

响应（application/json）：

```json
{
    "srcText": "" // 源文本字符串
}
```