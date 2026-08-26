# Spring设计模式

> 来源: https://notes.kamacoder.com/java/spring-design-patterns.html

# `# Spring设计模式 

## `# 简要回答 
  - Spring中使用的设计模式有**工厂设计模式、代理设计模式、单例模式、模版方法模式、包装器设计模式、观察者模式和适配器模式**等。   - 工厂模式：Spring通过BeanFactory和ApplicationContext等容器来创建和管理Bean对象，解耦对象的创建和使用。   - 单例模式：Spring中的Bean默认是**单例**的，Bean对象在Spring容器中唯一。   - 模版方法模式：Spring中如jdbcTemplate等以template结尾的类使用了**模版方法模式**，与Callback模式配合操作数据库。   - 观察者模式：Spring中的事件驱动模型使用了**观察者模式**，在一个事件触发时，会触发监听器，执行对应的方法。   - 代理模式：Spring AOP是基于**代理模式**的，SpringAOP的增强或通知需要使用适配器模式，Spring MVC中也使用**适配器模式**适配不同类型的Controller。 

## `# 详细回答 
  - 

**工厂模式** 
    - 工厂模式能够定义专门的工厂类来封装对象的创建逻辑，分离对象的创建与使用，从而降低耦合度。     - Spring可以通过**BeanFactory**创建Bean对象，能够实现最基本的依赖注入支持，采用懒加载机制，即在获取Beans时候才创建对象，占用内存较少，程序启动速度快。     - Spring可以使用**ApplicationContext**创建Bean对象，扩展了BeanFactory，支持更多的上下文特性，采用预加载机制，会在容器启动时一次性创建所有的Bean对象。ApplicationContext有三个实现类，分别是ClassPathXmlApplication、FileSystemXmlApplication和XmlWebApplicationContext。

      - ClassPathXmlApplicationContext从类路径下加载XML配置文件初始化容器       - FileSystemXmlApplicationContext从文件系统路径加载XML文件初始化容器       - XmlWebApplicationContext可以从Web应用中的XML文件加载上下文   - 

**代理模式** 
    - 代理模式为其他对象提供代理，控制对这个对象的访问，可以在不修改目标对象代码的前提下动态增强功能。     - Spring对代理模式的使用体现在**SpringAOP**中，SpringAOP将与业务无关，但多个业务模块所共同调用的逻辑封装，减少系统的重复代码。SpringAOP基于动态代理，有JDK和CGLIB两种代理方式，CGLIB代理基于继承，JDK代理基于接口。     - 客户端调用Subject接口的方法，实际调用的是代理类，代理类完成额外操作后调用目标类方法。   - 

**单例模式** 
    - 单例模式保证一个类只有一个实例，并提供一个全局访问点，可以避免重复创建消耗资源。     - Spring使用单例模式管理Bean对象，使用三级缓存机制保证Bean对象在Spring容器中的唯一性，Spring中的Bean默认是单例的。   - 

**模版方法模式** 
    - 模版方法定义了操作中的算法骨架，将算法的某些步骤延迟到子类中，模版方法使得子类可以不改变一个算法的结构即可重定义该算法的某些特定步骤。     - Spring中jdbcTemplate、hibernateTemplate等以Template结尾的类都使用了模版方法模式，Spring将固定的算法封装，将可变逻辑通过Callback接口暴露给用户，简化开发。   - 

**装饰者模式** 
    - 项目需要连接多个数据库，或者不同客户在每次访问中根据需要访问不同的数据库时，装饰者模式可以动态切换数据源。   - 

**观察者模式** 
    - 观察者模式可以定义对象之间一对多的依赖关系，实现当一个对象状态变化时，所有依赖它的对象会得到通知并自动更新，实现解耦通信。     - **Spring的事件驱动模型**是观察者模式的经典应用，包含三个核心组件：**事件**(ApplicationEvent)、**监听器**(ApplicationListener)、**发布者**(ApplicationEventPublisher)。定义事件时，实现ApplicationEvent接口，定义监听器时，实现ApplicationListener接口，事件发布者可以通过ApplicationEventPublisher的publishEvent()方法发布事件。   - 

**适配器模式** 
    - 适配器模式将一个类的接口转换成用户希望的另一个接口，让不同的类协同工作。     - Spring AOP的增强或通知需要使用适配器模式，AOP中每个类型的通知都有对应的拦截器，AOP执行时统一调用MethodInterceptor的invoke()方法，适配器会将具体的通知适配到MethodInterceptor中。     - Spring MVC中也使用适配器模式适配不同类型的Controller。SpringMVC中的HandlerAdapter**将不同类型处理器的调用接口转换成DispatcherServlet能识别的统一接口**，调用处理器的核心业务逻辑后返回ModelAndView结果。 

## `# 知识图解 
  - Spring中代理模式示意图
![image](../images/file1.kamacoder.com/i/bagu/20251129__E4_BB_A3_E7_90_86_E8_AE_BE_E8_AE_A1_E6_A8_A1_E5_BC_8F.jpg)
   - Spring AOP不同类型通知时机
![image](../images/file1.kamacoder.com/i/bagu/20251109_springAOP.jpg)
 

## `# 知识扩展 
  - 面试官可能追问 
  - Q1：Spring中的单例模式和传统单例模式有什么区别？

    - 传统的单例模式是通过私有构造器和静态方法保证的，创建逻辑固定，不支持依赖注入。     - Spring中的单例模式是通过BeanFactory或ApplicationContext创建Bean对象，多个容器可存在多个实例，由容器管理创建、依赖注入、销毁，支持懒加载和循环依赖解决。   - Q2：Spring的动态代理选择逻辑是什么？

    - Spring在目标类实现接口时**优先使用JDK代理**，目标类未实现接口时使用CGLIB代理，也可以通过spring.aop.proxy-target-class属性指定使用CGLIB代理。     - 基于JDK的动态代理，代理类需要实现InvocationHandler接口，通过invoke()方法反射来调用目标方法，将横切逻辑和业务编织在一起。Proxy类利用InvocationHandler动态创建一个符合某一接口的实例，生成目标类的代理对象。     - 基于CGLIB的动态代理，在代理类没有实现接口时使用，是由代码生成的类库，在运行时动态生成指定类的一个子类对象，覆盖其中特定方法并添加增强代码实现AOP。
