# SpringBoot概述

> 来源: https://notes.kamacoder.com/java/spring-boot-overview.html

# `# SpringBoot概述 

## `# 简要回答 
  - SpringBoot是Spring框架的简化版，通过**自动配置**减少XML配置内容，**起步依赖**整合常用的技术栈如SpringMVC、MyBatis等，**内置Tomcat**实现jar包的独立运行，解决Spring配置繁琐，依赖管理复杂的问题，使开发者专注业务而非框架配置。 

## `# 详细回答 
  - 

SpringBoot是基于Spring的**快速开发脚手架**。它提供一种快速启动的方式，自动配置和约定优于配置的原则极大地简化了Spring应用的搭建、开发和部署过程。   - 

SpringBoot使用**内嵌服务器**的方式，将Tomcat、Jetty等服务器嵌入到应用中，可以将应用程序打包成一个可执行的JAR文件，无需部署到外部容器，简化项目的部署和运行。   - 

SpringBoot采用**自动配置**的机制，根据应用程序中引入的依赖和配置，SpringBoot自动配置整个应用程序的环境。 
    - SpringBoot的自动配置是**基于条件的按需配置**，本质是通过注解驱动+SPI机制，根据项目依赖、环境配置、自定义规则，自动向IoC容器注入对应Bean，替代传统Spring的XML手动配置。     - **@EnableAutoConfiguration**是实现自动装配的核心注解，该注解中 **@AutoConfigurationPackage** 注解会将主应用程序类所在包及其子包下的所有类注册到IoC容器中，@Import注解会导入**AutoConfigurationImportSelector类** ，该类实现了ImportSelector接口，可以动态选择需要导入的自动配置类：在应用程序启动时，AutoConfigurationImportSelector类会**扫描类路径**，加载META-INF/spring.factories中的自动配置类，然后对每一个发现的自动配置类使用**条件判断**，通过条件注解（如@ConditionalOnClass）筛选出符合当前环境的配置类，如果满足导入条件，则将自动配置类注册到IoC容器中。遵循 “自定义优先” 原则，开发者可通过手动配置 Bean 或禁用自动配置类，覆盖默认行为，最终实现 “按需配置、简化开发” 的目标。   - 

SpringBoot提供了**快速的项目启动器**，不同的Starter将常用的技术栈的依赖整合，比如spring-boot-starter-web包含了SpringMVC、Jackson等Web开发常用的依赖，开发者只需引入一个依赖，无需手动管理版本，避免冲突。   - 

SpringBoot遵循**约定优于配置**的原则，预设默认的配置和约定，开发者按照这些约定进行开发，可以大大减少配置文件的编写。 
    - SpringBoot提供**特定的项目结构**，将主应用程序类置于根包，将控制器类、服务类、数据访问类等分别放在相应子包中，使开发者更易理解项目结构与组织，新成员加入项目也能快速定位各功能代码的位置，提升协作效率。     - SpringBoot提供了大量**默认配置**，比如连接数据库、设置Web服务器、处理日志等，开发者无需配置日志级别、输出格式与位置。     - SpringBoot的**自动化配置**也是约定大于配置的体现，通过分析项目的依赖和环境，自动配置应用程序的行为。 

## `# 知识图解 
  - Spring框架与Spring Boot的关系架构图
![image](../images/file1.kamacoder.com/i/bagu/20251206_SpringBoot_E9_A1_B9_E7_9B_AE_E7_BB_93_E6_9E_84.jpg)
 

## `# 知识扩展 
  - 扩展

    - SpringBoot的**生态支持**：提供spring-boot-actuator实现应用监控，进行健康检查与指标统计等；spring-boot-devtools实现热部署，开发时无需重启应用；spring-boot-test简化单元测试与集成测试，覆盖开发全生命周期。   - 面试官可能追问 
  - Q1：Spring和微服务的关系是什么？

    - SpringBoot是微服务架构的基础，单个微服务节点通常是一个SpringBoot应用；微服务治理框架(Spring Cloud)是基于SpringBoot实现的，Spring Cloud可以管理多个SpringBoot应用，通过Starter整合Eureka、Nacos等组件实现服务注册与发现、配置中心、熔断降级等能力。   - Q2：SpringBoot的自动配置可以禁用吗？

    - 可以禁用。在@SpringBootApplication中通过exclude属性来禁用，如@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})。还可以在配置文件中设置spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration。   - Q3：为什么SpringBoot的Starter能解决版本冲突？

    - SpringBoot维护了spring-boot-dependencies版本管理器，定义了所有Starter依赖的兼容版本；Starter引入时无需引入指定版本，由SpringBoot统一管控可以避免手动引入不同版本依赖的冲突。   - Q4：自动配置的条件注解优先级怎么排？

    - 条件注解按照从类到方法的层级进行执行，同一层级内的条件注解按照代码顺序执行。如果某个类/方法上有条件注解失败，则该类/方法会失效。
