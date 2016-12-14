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
     
