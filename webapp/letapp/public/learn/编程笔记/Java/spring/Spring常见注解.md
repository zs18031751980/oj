# Spring常见注解

> 来源: https://notes.kamacoder.com/java/spring-annotations.html

# `# Spring常见注解 

## `# 简要回答 
  - Spring核心注解可以进行**Bean管理、依赖注入、AOP、事务和Web**等场景。   - Bean注册时可以使用@Component或者使用@Service、@Repository、@Controller标记组件。   - 依赖注入时可以使用@Autowired按类型注入或者使用@Resource按名称注入，还可以使用@Qualifier指定名字。   - @Aspect可以标记切面，@Transactional可以声明事务。   - 与Web相关注解有@RequestMapping用于请求映射，@RequestBody接收请求体，@ResponseBody返回响应体。 

## `# 详细回答 
  - Spring框架提供了很多注解，可以用于简化配置，管理Bean、处理事务和处理AOP等。   - @Component：Spring的组件注解，将一个类标识为Spring的组件，通过组件扫描可以向Spring注册Bean。   - @ **Bean**：也是向Spring声明Bean，在配置类中使用，Spring容器会根据配置类中@ Bean方法返回的实例来管理Bean。   - @ **Autowired**：用于自动注入依赖项，可以在构造器、Setter方法和字段上，Spring会自动查找匹配类型的Bean进行注入。   - @ **Qualifier**：与@ Autowired一起使用，指定注入时使用的Bean名称。   - @ **Primary**：在没有使用Qualifier注解，优先注入Primary的实例。   - @ **Value**：用于从属性文件或配置中读取值，将值注入到成员变量中。   - @ **Service**、@ **Repository和**@ **Controller服务层**、持久层和控制层的Bean，也是比较明确的Component。   - @ **Controller**：将类标记为控制器，用于处理HTTP请求。   - @ **RestController**：用于构建RESTful Web服务，类的所有处理器方法返回值会被自动序列化，写入HTTP响应体。   - @ **Configuration**：用于定义配置类，替代XML配置文件，其中定义的Bean会被Spring容器管理。   - @ **RequestMapping**：将HTTP请求路径映射到Controller的处理方法上，定义请求的URL路径、请求方法和参数。   - @ **RequestBody**：可以读取Request请求的Body部分，接受客户端传递的JSON、XML格式的数据并自动绑定到Java对象上，应用于RESTful接口的开发。   - @ **GetMapping**、@ **PutMapping**、@ **DeleteMapping**用于处理对应的HTTP请求，简化了RequestMapping。   - @ **PostMapping**：处理post请求，@ PostMapping 通常与 @ RequestBody 配合，用于接收 JSON 数据并映射为 Java 对象。   - @ **PathVariable**：可以从URL路径中提取参数。 

## `# 知识图解 

![Spring常见注解示意图](../images/file1.kamacoder.com/i/bagu/20251109_spring_E6_B3_A8_E8_A7_A3.jpg)
 

## `# 知识扩展 
  - 面试官可能追问： 
  - 

@ Component和@ Bean注册的Bean有什么本质区别？ 
    - @ Component是类注解扫描，Spring会通过类路径扫描**自动实例化**，依赖无参构造；@ Bean可以进行**手动定义**，开发者可以自定义实例化的逻辑，根据@ Bean方法返回的实例来管理Bean。     - 如果同一类型的Bean被两种方式注册，Bean会覆盖Component的，因为**Bean是显式配置，优先级更高**。   - 

如果一个类既引用了@ Service又在@ Configuration中使用@ Bean定义了该类的实例，容器中会有几个Bean?分别是什么名称？ 
    - 使用Service没有指定名称时默认类名是首字母小写，而Bean的默认名称是方法名，如果产生了名称冲突，@ Bean注解定义的Bean会覆盖Service注解，容器中只有一个Bean，如果Bean注解指定了不同的名称那么容器中会有两个Bean。   - 

@ Autowired和@ Resource有什么区别？Autowired什么时候会报错？ 
    - @ Autowired是Spring的原生注解，默认会按类型匹配，@ Resource是JDK注解，是优先按照名称匹配的。     - 当Autowired没有找到匹配类型的Bean时会报错NoSuchDefinitionException，需要设置required=false，将变量赋值为null，但是后续代码需要判断该Bean是否为空。   - 

@ RestController和@ Controller有什么区别？如果@ Controller想返回JSON可以怎么做？ 
    - RestController注解是Controller注解和ResponseBody注解的结合，类中的所有方法默认返回JSON；所以在有Controller注解的方法上添加@ ResponseBody注解可以返回JSON。
