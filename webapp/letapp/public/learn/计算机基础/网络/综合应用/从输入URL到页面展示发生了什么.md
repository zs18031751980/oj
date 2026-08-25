# 从输入URL到页面展示发生了什么

> 来源: https://notes.kamacoder.com/base/url-to-page-rendering.html

# 从输入URL到页面展示发生了什么

## 简要回答

  1. **URL解析**：

浏览器从URL中解析出主机名（如`www.baidu.com`）。
   2. **DNS查询**：

浏览器先查询本机**hosts**文件，若未找到则转向外网DNS服务器查询。
   3. **建立TCP连接**：

浏览器与服务器通过三次握手建立TCP连接。
   4. **发送HTTP请求**：

浏览器通过TCP连接向Tomcat发送HTTP请求。
   5. **Tomcat处理请求**：

Tomcat查询**web.xml**配置文件，找到对应的Servlet并调用其service()方法。
   6. **Servlet处理请求**：

Servlet实例处理请求，生成响应数据并返回给Tomcat。
   7. **返回HTTP响应**：

Tomcat将响应数据打包成HTTP响应，通过TCP连接返回给浏览器。
   8. **浏览器渲染页面**：

浏览器解析HTTP响应，渲染HTML、CSS和JavaScript，并最终展示页面。

## 详细回答

  1. **URL解析**：

    - **过程**：
浏览器从URL中解析出**主机名**（如 www.baidu.com）；浏览器还会解析出**协议**（如http 或 https）、**端口号**（如80 或 443）和**路径**（如/index.html）。
     - **作用**：
确定请求的 目标服务器 和 资源位置。

   2. **DNS查询**：

    - **过程**：

① 浏览器检查本机**hosts文件**（路径为`C:\Windows\System32\drivers\etc\hosts`），查找主机名对应的**IP地址**。

② 如果hosts文件中未找到，浏览器向**本地DNS服务器**发送查询请求。

③ 本地DNS服务器依次向**根DNS服务器、顶级域名服务器和权威DNS服务器**查询，最终获取IP地址。如果DNS查询失败，浏览器会提示“找不到网站”（如`DNS_PROBE_FINISHED_NXDOMAIN`）。
     - **作用**：
将主机名解析为IP地址，以便浏览器与服务器建立连接。

   3. **建立TCP连接**：

    - **三次握手**：

① 浏览器向服务器发送`SYN`报文，请求建立连接。

② 服务器回复`SYN-ACK`报文，表示同意建立连接。

③ 浏览器回复`ACK`报文，表示连接已建立。
     - **TLS握手（HTTPS）**：
如果使用HTTPS协议，浏览器和服务器还会进行TLS握手，协商加密算法并交换密钥。
     - **作用**：
建立**可靠的、面向连接的**通信通道，确保数据可靠传输。

   4. **发送HTTP请求**：

    - **过程**：

①浏览器通过已建立的TCP连接发送HTTP请求。

②HTTP请求包括：- **请求行**：如`GET /index.html HTTP/1.1`。- **请求头**：如`Host: www.baidu.com`、`User-Agent: Mozilla/5.0`。- **请求体**：如POST请求中的表单数据。
     - **作用**：
向服务器请求指定的资源。

   5. **Tomcat处理请求**：

    - **接收请求**：

Tomcat通过TCP连接接收来自浏览器的HTTP请求。
     - **查询web.xml**：

      - Tomcat查询web.xml配置文件，查看请求的资源是否在`<servlet-mapping>`的**url-pattern**配置中。
       - 如果找到对应的url-pattern，则获取`<servlet-name>`。

     - **查找Servlet实例**：

      - Tomcat维护了**两个HashMap**容器：

① HashMap<**id, Servlet**>：以`<servlet-name>`为键，存储Servlet实例。

② HashMap<**url-pattern, servlet-name**>：以`<url-pattern>`为键，存储`<servlet-name>`。
       - 如果未找到对应的Servlet实例，Tomcat根据`<servlet-name>`获取`<servlet-class>`中的**全类名**，通过**反射技术**实例化Servlet，并调用 **init()方法** 完成初始化。

     - **调用 service() 方法**：

      - Tomcat调用Servlet的 **service()方法**，处理请求并生成响应数据。

     - **作用**：

处理请求并生成响应数据。

   6. **Servlet处理请求**：

    - **创建请求和响应对象**：

Tomcat为每次请求创建一个新的 **HttpServletRequest** 对象和一个新的 **HttpServletResponse** 对象。
     - **调用service()方法**：

Servlet的 **service()方法** 根据请求方式（如**GET** 或 **POST**）调用 **doGet()** 或 **doPost()** 方法。
     - **生成响应数据**：

Servlet将处理结果写入**HttpServletResponse**对象中。
     - **PS**：

Servlet是**单例**的，但 service()方法 是**多线程**的，因此需要注意线程安全问题。
     - **作用**：

处理请求并生成响应数据。

   7. **返回HTTP响应**：

    - Tomcat将 **HttpServletResponse** 对象中的内容打包成HTTP响应。
     - HTTP响应包括：

      - **状态行**：如`HTTP/1.1 200 OK`。
       - **响应头**：如`Content-Type: text/html`、`Content-Length: 1024`。
       - **响应体**：如HTML内容。

     - Tomcat通过**TCP连接**将HTTP响应返回给浏览器。
     - **作用**：将处理结果返回给浏览器。

   8. **浏览器渲染页面**：

    - **解析HTML**：

浏览器解析HTML文档，构建DOM树。
     - **解析CSS**：

浏览器解析CSS文件，构建CSSOM树。
     - **执行JavaScript**：

浏览器执行JavaScript代码，可能会修改DOM树和CSSOM树。
     - **构建渲染树**：

浏览器将DOM树和CSSOM树合并为渲染树。
     - **布局和绘制**：
浏览器根据渲染树计算布局，并将页面内容绘制到屏幕上。
     - **PS**：

浏览器对静态Web资源（html,css,js,图片等）的请求实际是由Tomcat的**DefaultServlet**来完成的， 当其他的url-pattern都匹配不上时，Tomcat就通过DefaultServlet来拦截到其它静态资源。
     - **作用**：

将HTTP响应中的内容渲染为可视化的页面。

## 知识拓展

### HTTP的概念

  - HTTP：**全称HyperTextTransferProtocol**，指超文本传输协议；HTTP是互联网上应用广泛的一种网络协议。HTTP 是TCP/IP协议栈的一个应用层协议，是**工作在TCP/IP协议（网络传输协议）基础上**的，所有的WWW文件都遵守这个标准。其中，HTTP1.0短连接，HTTP1.1长连接。

### HTTP1.0短连接 和 HTTP1.1长连接 的区别

  - **HTTP/1.0短连接**：

    - **定义**：

在HTTP/1.0中，默认情况下，每次HTTP请求完成后会关闭TCP连接。
     - **过程**：

① 浏览器与服务器通过三次握手建立TCP连接。

② 浏览器发送HTTP请求，服务器返回HTTP响应。

③ 服务器关闭TCP连接。
     - **缺点**：

① **性能开销大**：每次请求都需要建立和关闭TCP连接，增加了延迟和资源消耗。

② **不适合频繁请求**：对于需要多次请求的页面（如加载多个资源），性能较差。

   - **HTTP/1.1长连接**：

    - **定义**：

在HTTP/1.1中，默认使用长连接（`Connection: keep-alive`），允许在同一个TCP连接上发送多个HTTP请求和响应。
     - **过程**：

① 浏览器与服务器通过三次握手建立TCP连接。

② 浏览器发送多个HTTP请求，服务器返回多个HTTP响应。

③ 当连接空闲一段时间后，服务器或浏览器会关闭TCP连接。
     - **优点**：

① **减少连接开销**：复用TCP连接，减少了建立和关闭连接的开销。

② **提高性能**：适合需要多次请求的页面（如加载多个资源）。
     - **缺点**：
 **连接管理复杂**：需要处理连接的复用和超时关闭。

### HTTPS 和 HTTP 的区别

  - **HTTP**：

    - **定义**：

HTTP（HyperText Transfer Protocol）是应用层协议，用于在浏览器和服务器之间传输超文本（如HTML、CSS、JavaScript等）。
     - **特点**：

① **明文传输**：数据以明文形式传输，容易被窃听或篡改。

② **无加密**：不提供数据加密和身份验证。

③ **默认端口**：`80`。

   - **HTTPS**：

    - **定义**：

HTTPS（HyperText Transfer Protocol Secure）是**HTTP的安全版本**，通过 TLS/SSL 协议对数据进行**加密**和**身份验证**。
     - **特点**：

① **加密传输**：数据通过 TLS/SSL 协议加密，防止窃听和篡改。

② **身份验证**：通过数字证书验证服务器身份，防止中间人攻击。

③ **默认端口**：`443`。
     - **工作原理**：

      1. **TLS（Transport Layer Security）握手**：

① 客户端（浏览器）向服务器发送**ClientHello**消息，包含支持的TLS版本和加密算法。

② 服务器回复**ServerHello**消息，选择TLS版本和加密算法，并发送数字证书。

③ 客户端验证证书，生成会话密钥，并使用服务器的公钥加密后发送给服务器。

④ 服务器使用私钥解密会话密钥，双方开始加密通信。
       2. **加密通信**：

客户端和服务器端使用 会话密钥 加密和解密数据。
