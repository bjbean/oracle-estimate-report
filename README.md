#### 很多公司考虑将Oracle数据库，逐步迁移到其他数据库。需要开发人员和DBA快速了解现有Oracle的使用情况，并据此评估工作量、迁移难度等。特开发此脚本，简化工作，可快速生成报告。可直观看到可能的迁移工作量

### 1.功能
显示指定数据库的对象、资源、SQL等情况，并据此进行迁移分析判断工作。

### 2.使用方法
#### 配置文件
        [database]
        server       = 127.0.0.1
        port         = 1521
        db_user      = system
        db_pwd       = xxx
        db_name      = testdb
        analyze_user = test_user         #分析用户名
        service_name = testdb            #用户对应服务名

        [parameters]
        table_max_size = n              #单表大小(单位MB)
        table_row_num  = n              #表的记录数
        long_sql_size  = n              #SQL语句过长标准(单位字符)
        
#### 调用方法
        python osr.py             #概要模式生成报告
        python otom.py –o detail  #详细模式生成报告
        
#### 输出文件
        在脚本同目录下，会生成HTML报告文件。可参见demo.htm。
### 3.报告解读     
        下面以迁移至MySQL数据库为例进行说明。
#### 空间使用情况
        空间大小是迁移MySQL数据库需重点考虑的指标之一。如库较大，应考虑应用层做拆分（水平or垂直）或在MySQL考虑使用分库分表技术。    
#### 对象使用情况
        【表】：数量过多，应考虑分库。
        【表(大表)】：表过大，应考虑采用分表或者分库方式改造。大表判断规则是通过配置文件设置的。
        【表(分区表)】：不建议在MySQL中使用分区表。如Oracle中使用了分区表，MySQL中考虑改造。
        【字段(大对象)】：不建议在MySQL中使用大对象字段，考虑改造。
        【索引(B树)】：索引过多会影响效率。如该指标过大，需分析具体情况。
        【索引(其他)】：MySQL不支持其他类别索引，考虑改造。
        【视图】：不建议在MySQL中使用视图，考虑改造。
        【触发器】：不建议在MySQL中使用触发器，考虑改造。
        【存储过程】：不建议在MySQL中使用存储过程，考虑改造。
        【函数】：不建议在MySQL中使用函数，考虑改造。
        【序列】：MySQL中是通过自增长属性实现的。如并发量较大，考虑通过应用端实现。
        【同义词】：同义词是数据耦合的表现，考虑在业务端进行拆分。
#### 对象DML次数
        对象DML次数直接反应了繁忙程度。如DML次数非常多的对象，需要在迁移至MySQL时重点评估其性能表现。
#### 整体资源消耗
        列出了最近24小时的资源使用情况，供用户评估现有资源使用情况。
        对于某项指标非常突出的情况，那说明现有业务也有瓶颈，在迁移至MySQL时尽量在设计阶段就予以考虑。
#### SQL
        这部分收集了分析用户在历史的所有SQL。
        【总SQL数】：该指标可近似反映业务繁忙程度，此外可用于后续有问题语句的比例分析基础。
        【超长SQL】：超过指定字符数的语句，阀值在配置文件中设置。MySQL建议使用“短小精悍”的SQL，复杂SQL变现不佳。这些语句建议改造。
        【ANTI SQL】：反向查询是MySQL不擅长的，建议修改写法。
        【Oracle Syntax SQL】：有Oracle特征的写法（例如特有函数、伪列等），需要在迁移至MySQL时修改。
        【Join 3+ Table SQL】：MySQL表间关联效率很低，不建议使用超过2个以上表的关联。这里列出的是3个及以上的关联查询，需要考虑修改。
        【SubQuery SQL】：子查询也是MySQL不擅长的，建议修改写法。
#### 规则说明
        * 大表判断规则1_物理大小: 1000 M
        * 大表判断规则2_记录数: 1000000
        * SQL超长标准: 200 字符
        * ANTI SQL: 指包含关键字(not in、not exist)的语句
        * Oracle Syntax SqL: 指包含关键字(rowid、rownum、decode、partition、rullup、cube、sampling、rank、percentile、ntitle、top、bottom、period、lead、lag的语句
        * Join 3+ Table SQL: 关联3个及3个以上表的语句
        * SubQuery SQL: 包含子查询的语句 
