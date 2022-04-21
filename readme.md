# 基于“学小易”搜题 API 的学习通答题/考试油猴脚本题库代理

适用于 TamperMonkey 用户脚本：[超星网课助手/刷课/搜题（支持图片）/考试/all in one(fake题)](https://greasyfork.org/zh-CN/scripts/431514)

解决公共题库失效或接口风控导致的无法搜题，使用抓包和反编译取得“学小易”客户端的搜题接口，用于转发搜题请求返回脚本正确答案，从而达到代替公共题库接口

# 准备食材

- Python3.6+

- Flask

- Protobuf Python lib

- Protoc（Protobuf 结构体编译器）

- 任何基于 chrome/firefox 的浏览器

- TamperMonkey 插件

- TamperMonkey 用户脚本：[超星网课助手/刷课/搜题（支持图片）/考试/all in one(fake题)](https://greasyfork.org/zh-CN/scripts/431514)

# 处理食材

## 编译 Protobuf 结构体

因学小易 API 的数据序列化格式为 Protobuf，所以务必编译 proto 结构体

```bash
protoc -I. --python_out=. xuexiaoyi.proto
```

执行后得到`xuexiaoyi_pb2.py`，该模块为学小易 API 数据的 descriptor

## 修改用户脚本

将该用户脚本的`api_array`中的主机名改成你的服务端 ip 并使用88端口，同时注释掉原公共题库 url

这里用`192.168.1.3`举例

```javascript
const api_array = [
    //"http://ti.fakev.cn/hashTopic?question=",
    "http://192.168.1.3:88/hashTopic?question="
];
```

再加入跨域白名单

这里用`192.168.1.3`举例

```javascript
// @connect      ti.fakev.cn
// @connect      192.168.1.3
```

### 关于加密字体

如果有加密字体解析需求，清自行向`font_hashmap.db`中添加字形hash，并修改用户脚本`findAnswer()`函数下内容

```javascript
    // 拾取加密字体
    var secFont = '';
    if($TiMu.find(".font-cxsecret").length != 0){
        secFont = $("style[type='text/css']").text().match(/'(data:application\/font-ttf;.*?)'/)[1];
    }
    // 回传答案用以后端命中
    var answers = $TiMu.find("a"),
        answersText='';
    for(var i=0;i<answers.length;i++){
        answersText += ('#'+filterImg(answers.eq(i)));
    }
    GM_xmlhttpRequest({
        method: "POST",
        url: api_array[setting.api],
        data:'question='+encodeURIComponent(question)+'&answers='+encodeURIComponent(answersText)+'&secFont='+encodeURIComponent(secFont),
```

字体加密的效果如下(去掉了文本的`.font-cxsecret`属性)

![](http://i0.hdslb.com/bfs/album/063c3182c89dd22878bf783f71d9b08929b135f1.png)

# 做菜

启动服务端

```bash
python3 app.py
```

服务端启动后将监听88端口，这里本地 ip 以`192.168.1.3`为例

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
