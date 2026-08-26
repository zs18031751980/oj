# Spring IOC

> 来源: https://notes.kamacoder.com/java/spring-ioc.html

# `# Spring IOC 

## `# 简要回答 
  - SpringIOC是**控制反转的设计思想**，原先由程序员控制整个程序的执行，使用IOC思想后将控制权交给了IOC容器，由Spring **IOC容器来控制Bean的生命周期**，**对象的创建、初始化和销毁**。在程序中不手动new对象，而是通过@ Component或@ Autowired注解来配置，容器会自动实例化Bean，注入依赖，降低代码耦合，简化开发。 

## `# 详细回答 

### `# IOC定义 
  - IOC是Inversion of Control的缩写，即控制反转，是一种设计思想。传统的开发中需要开发者手动new对象，维护依赖关系；在IOC模式下，它将设计好的对象交给IOC容器控制，由容器统一管理Bean的生命周期（对象的创建、初始化和销毁过程）及其依赖关系。 

### `# IOC作用 
  - IOC容器管理对象之间的相互依赖关系和对象的注入，可以简化应用的开发，让资源容易管理。同时降低对象之间的耦合度，在创建对象时只需写配置文件或注解，无需编写创建过程的代码。   - 例如：在项目中的一个Service类中，可能会有多个类作为其底层，这些类之间可能会有依赖关系，IOC容器可以自动管理这些依赖关系，将依赖的对象注入到Service类中，无需清楚所有底层类的构造函数。 

### `# IOC容器的实现与Bean注册/注入方式 
  - IOC容器会利用**反射机制**动态加载类，创建对象实例和调用对象方法；通过**依赖注入**让容器管理应用程序组件之间的依赖关系；通常使用**BeanFactory或ApplicationContext**来创建IOC容器，并管理Bean实例。   - 在Spring中，传统使用**配置注册**，即使用XML进行配置，将Bean注册到IOC容器中，并指定Bean的属性。现在，SpringBoot**注解注册**已经成为主流，开发者可以使用@Component、@Service、@Controller、@Repository等注解来实现自动扫描配置Bean，@Configuration和@Bean可以手动注册第三方组件，无需编写XML文件。   - IOC**依赖注入**的方式有注解注入、构造器注入和Setter方法注入三中。使用@Autowired可以按类型注入、@Qualifier可以按名称注入、@Resource可以按名称或类型注入；在构造器注入中，Bean构造器参数标注@Autowired，在Spring4.3后，已经变成默认的注入方式；Setter方法注入中，Bean的Setter方法标注@Autowired。 

### `# IOC容器启动流程 
  - 先**创建SpringIOC容器**，也就是ApplicationContext或BeanFactory。   - 容器通过ResourceLoader**加载**配置文件，ResourceResolver**解析**资源并生成Resource对象。   - 将生成的Resource对象，通过BeanDefinitionReader进行解析，将Bean定义信息**生成BeanDefinition对象**。   - 将BeanDefinition对象通过BeanRegistry**注册到容器**中,此时容器的初始化完成。 

### `# IOC容器管理Bean 
  - 容器会加载配置（注解/XML）文件，扫描需要注册的Bean；随后通过反射**创建Bean实例**，并完成**依赖注入**；   - 调用@PostConstruct注解的方法或者自定义方法进行**初始化**；   - 将**Bean存入容器**，开发者可以通过getBean()或注解注入使用；在容器关闭时调用@PreDestroy注解的方法或者自定义方法进行销毁； 

## `# 知识图解 
  - IOC容器功能示意图
![image](/learn/编程笔记/Java/images/file1.kamacoder.com/i/bagu/20251116_spring_IOC.jpg)
 

## `# 知识扩展 
  - 面试官可能追问？ 
  - Q1：BeanFactory和ApplicationContext的区别是什么？

    - **BeanFactory**是Spring最原始的IOC容器，**ApplicationContext**是BeanFactory的增强版，提供了更多的功能，如资源加载、国际化、事件发布等。   - Q2：如果两个Beann之间存在**循环依赖**，SpringIOC怎么处理？

    - Spring通过**三级缓存**可以解决构造器注入之外的循环依赖问题。三级缓存分别是singletonObjects成品Bean缓存、earlySingletonObjects临时Bean缓存（半成品缓存）和singletonFactories工厂缓存，用于生成半成品Bean。通过在Bean实例化后，依赖注入前将其早期引用存入缓存，让依赖它的Bean能够提前获取引用，打破循环阻塞。     - 如果是构造器注入的循环依赖，Spring会抛出BeanCurrentlyInCreationException异常，因为构造器注入需要实例化依赖Bean，导致循环阻塞。将构造器注入改成字段注入或Setter注入，或者使用@Lazy注解延迟其中一个Bean的实例化可以解决。   - Q3：ApplicationContext加载配置时，Bean是立即实例化还是延迟实例化？可以控制吗？

    - 默认情况下，**ApplicationContext会在容器启动时实例化所有单例Bean**，如果想实现延迟实例化，需要在类或@Bean方法上使用 **@Lazy注解** ，此时singleton Bean会延迟到第一次被使用时实例化。     - @Lazy对单例Bean有效，prototype Bean本身就是懒加载。
