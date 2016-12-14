#!/usr/bin/python
# -*- coding: utf-8 -*-

"""************************************************************

=====配置文件=====
[database]
server      = 127.0.0.1
port        = 1521
db_user     = testuser
db_pwd      = testpwd
db_name     = test
service_name= testdb

[parameters]
table_max_size = n      #单表大小(单位MB)
table_row_num = n       #表的记录数
long_sql_size = n       #SQL语句过长标准
************************************************************"""

import sys
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
import pprint
import ConfigParser
import cx_Oracle
import getopt
from pyh import *
import time
import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML

reload(sys)
sys.setdefaultencoding("utf-8")

def is_subselect(parsed):
    if not parsed.is_group():
        return False
    for item in parsed.tokens:
        if item.ttype is DML and item.value.upper() == 'SELECT':
            return True
    return False

def extract_from_part(parsed):
    from_seen = False
    for item in parsed.tokens:
        #print item.ttype,item.value
        if from_seen:
            if is_subselect(item):
                for x in extract_from_part(item):
                    yield x
            elif item.ttype is Keyword:
                raise StopIteration
            else:
                yield item
        elif item.ttype is Keyword and item.value.upper() == 'FROM':
            from_seen = True

def extract_table_identifiers(token_stream):
    for item in token_stream:
        if isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                if isinstance(identifier,Identifier):
                    yield identifier.get_real_name()
        elif isinstance(item, Identifier):
            yield item.get_real_name()
        # It's a bug to check for Keyword here, but in the example
        # above some tables names are identified as keywords...
        elif item.ttype is Keyword:
            yield item.value

def extract_tables(p_sqltext):
    stream = extract_from_part(sqlparse.parse(p_sqltext)[0])
    return list(extract_table_identifiers(stream))

def print_html_header():
    page = PyH('')
    page << """<head>
            <meta http-equiv="Content-Type" content="text/html;" charset="utf-8" />
            </head>"""
    page << """<style type="text/css">
            body.awr {font:bold 10pt Arial,Helvetica,Geneva,sans-serif;color:black;}
            pre.awr  {font:10pt Courier;color:black; background:White;}
            h1.awr   {font:bold 20pt Arial,Helvetica,Geneva,sans-serif;color:#336699;border-bottom:1px solid #cccc99;margin-top:0pt; margin-bottom:0pt;padding:0px 0px 0px 0px;}
            h2.awr   {font:bold 18pt Arial,Helvetica,Geneva,sans-serif;color:#336699;margin-top:4pt; margin-bottom:0pt;}
            h3.awr   {font:bold 16pt Arial,Helvetica,Geneva,sans-serif;color:#336699;margin-top:4pt; margin-bottom:0pt;}
            h4.awr   {font:bold 14pt Arial,Helvetica,Geneva,sans-serif;color:#336699;margin-top:4pt; margin-bottom:0pt;}
            h5.awr   {font:bold 12pt Arial,Helvetica,Geneva,sans-serif;color:#336699;margin-top:4pt; margin-bottom:0pt;}
            h6.awr   {font:bold 10pt Arial,Helvetica,Geneva,sans-serif;color:#336699;margin-top:4pt; margin-bottom:0pt;}
            h7.awr   {font: 10pt Arial,Helvetica,Geneva,sans-serif; color:#336699;margin-top:4pt; margin-bottom:0pt;}
            li.awr   {font:bold 12pt Arial,Helvetica,Geneva,sans-serif; color:black; background:White;}
            th.awrnobg  {font:bold 10pt Arial,Helvetica,Geneva,sans-serif; color:black; background:White;padding-left:4px; padding-right:4px;padding-bottom:2px}
            td.awrbg    {font:bold 10pt Arial,Helvetica,Geneva,sans-serif; color:White; background:#0066CC;padding-left:4px; padding-right:4px;padding-bottom:2px}
            td.awrnc    {font:10pt Arial,Helvetica,Geneva,sans-serif;color:black;background:White;vertical-align:top;}
            td.awrc     {font:10pt Arial,Helvetica,Geneva,sans-serif;color:black;background:#FFFFCC; vertical-align:top;}
            a.awr       {font:bold 10pt Arial,Helvetica,sans-serif;color:#663300; vertical-align:top;margin-top:0pt; margin-bottom:0pt;}
            </style>"""
    page << """<SCRIPT>
            function isHidden(oDiv,oTab){
              var vDiv = document.getElementById(oDiv);
              var vTab = document.getElementById(oTab);
              vDiv.innerHTML=(vTab.style.display == 'none')?"<h5 class='awr'>-</h5>":"<h5 class='awr'>+</h5>";
              vTab.style.display = (vTab.style.display == 'none')?'table':'none';
            }
            </SCRIPT>"""
    

    page << h1('Oracle数据库迁移评估报告',cl='awr')
    page << br()
    return page

def query_sql(p_dbinfo,p_sql):
    db = p_dbinfo
    conn=cx_Oracle.connect(db[3]+'/'+db[4]+'@'+db[0]+':'+db[1]+'/'+db[2])
    cursor = conn.cursor()
    cursor.execute(p_sql)
    records = list(cursor.fetchall())   
    cursor.close()
    conn.close()
    return records

def print_html_table(p_page,p_title,p_data):
    l_page = p_page
    l_data = p_data
    l_header = p_title
    
    mytab = l_page << table(border='1',width=800)
    headtr = mytab << tr()
    for i in range(0,len(l_header)):
        td_tmp = headtr << td(l_header[i])
        td_tmp.attributes['class']='awrbg'
        td_tmp.attributes['align']='center'

    for j in range(0,len(l_data)):
        tabtr = mytab << tr()
        for i in range(0,len(l_data[j])):
            td_tmp = tabtr << td(l_data[j][i])
            td_tmp.attributes['class']='awrc'
            td_tmp.attributes['align']='right'
            if j%2==0:
                td_tmp.attributes['class']='awrc'
            else:
                td_tmp.attributes['class']='awrnc'
    l_page << br()

def query_ora_obj_size_by_num(p_dbinfo,p_schema_name,p_num):
    db = p_dbinfo
    conn=cx_Oracle.connect(db[3]+'/'+db[4]+'@'+db[0]+':'+db[1]+'/'+db[2])
    cursor = conn.cursor()
    cursor.execute("select * from (select (case s.segment_type when 'TABLE PARTITION' then partition_name else segment_name end ) object_name, s.segment_type, (case s.segment_type when 'TABLE' then s.segment_name when 'INDEX' then (select i.table_name from dba_indexes i where i.owner=s.owner and i.index_name=s.segment_name) when 'LOBSEGMENT' then (select l.table_name||':'||l.column_name from dba_lobs l where l.owner=s.owner and l.segment_name=s.segment_name) else s.segment_name end ) parent_name,round(s.bytes/1024/1024/1024,2) size_gb from dba_segments s where s.owner='"+p_schema_name+"' and s.segment_name not like 'BIN%' order by 4 desc) where rownum<="+p_num)
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return records

def print_help():
    print "Usage:"
    print "    ./otom.py -o <summary|detail>"
    print "    -o : summary|detail"

if __name__ == "__main__":    
    
    # initial variable    
    v_dbinfo = []
    v_username=''
    v_date=''
    v_option=''
    v_parameters = {}
    v_conf=sys.path[0]+"/osr.conf"
    v_rpt_filename=''    
    v_analyze_user=''
    v_results = []
    v_data = []

    # deal input parameter
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:")

        for o,v in opts:
            if o == "-o":
                v_option=v.upper()
    except getopt.GetoptError,msg:
        print_help()
        exit()            

    # initial database config file
    config = ConfigParser.ConfigParser()
    config.readfp(open(v_conf))
    for section in config.sections():
        if section == "database":
            v_dbinfo=[config.get(section,'server'),config.get(section,'port'),config.get(section,'db_name'),config.get(section,'dba_user'),config.get(section,'dba_pwd')]
            v_analyze_user=config.get(section,'analyze_user').upper()
            v_parameters['service_name']=config.get(section,'service_name')
        else:
            for attr in config.options(section):
                v_parameters[attr]=config.get(section,attr)
    #pprint.pprint(v_parameters)
    #pprint.pprint(v_dbinfo)

    # initial other variable
    v_date = time.strftime('%Y-%m-%d')    
    v_rpt_filename = 'rpt_db_'+v_dbinfo[0].replace('.','_')+'_'+v_dbinfo[2]+'_'+v_analyze_user.lower()+'_'+v_date.replace('-','')+'.html'
    
    # get html global object
    v_page = print_html_header()
    
    # output general info
    v_page << h5('数据库概要信息',cl='awr')
    print_html_table(v_page,['数据库IP/域名','数据库实例','分析用户','分析时间'],[[v_dbinfo[0],v_dbinfo[2],v_analyze_user,time.strftime('%Y-%m-%d')]])

    #output database size
    v_page << h5('空间使用情况',cl='awr')
    v_results=query_sql(v_dbinfo,"select round(sum(bytes)/1024/1024,2) from dba_segments where owner='"+v_analyze_user+"'")

    print_html_table(v_page,['用户名','空间使用(MB)'],[[v_analyze_user,v_results[0][0]]])
    
    #output object info
    v_page << h5('对象使用情况',cl='awr')
    #--query table num
    v_results=query_sql(v_dbinfo,"select count(*) from dba_tables where owner='"+v_analyze_user+"'")    
    v_data.append(['表',v_results[0][0]])

    #--query big table
    SQL_BIG_TABLE="""
    select table_name from dba_tables t1 where t1.owner='"""+v_analyze_user+"""' and t1.NUM_ROWS>"""+v_parameters['table_row_num']+"""
    union
    select segment_name from dba_segments s1 where s1.owner='"""+v_analyze_user+"""' and s1.segment_type='TABLE' and s1.BYTES>"""+str(int(v_parameters['table_max_size'])*1000*1000)
    v_results=query_sql(v_dbinfo,SQL_BIG_TABLE)
    v_data.append(['表(大表)',len(v_results)])
    if v_option=="DETAIL":
        v_big_table = v_results

    #--query partition table
    SQL_PART_TABLE="""
    select table_name from dba_tables where owner='"""+v_analyze_user+"""' AND PARTITIONED='YES'
    """
    v_results=query_sql(v_dbinfo,SQL_PART_TABLE)
    v_data.append(['表(分区表)',len(v_results)])
    if v_option=="DETAIL":
        v_part_table = v_results

    #--query lob column
    SQL_LOB_COLUMN="""
    select table_name,column_name from dba_lobs where owner='"""+v_analyze_user+"""'
    """
    v_results=query_sql(v_dbinfo,SQL_LOB_COLUMN)
    v_data.append(['字段(大对象)',len(v_results)])
    if v_option=="DETAIL":
        v_lob_column = v_results

    #--query btree index
    SQL_BTREE_INDEX="""
    select count(*) from dba_indexes where owner='"""+v_analyze_user+"""' and index_type='NORMAL'
    """
    v_results=query_sql(v_dbinfo,SQL_BTREE_INDEX)
    v_data.append(['索引(B树)',v_results[0][0]])

    #--query other index
    SQL_OTHER_INDEX="""
    select table_name,index_name,index_type from dba_indexes where owner='"""+v_analyze_user+"""' and index_type!='NORMAL'
    """
    v_results=query_sql(v_dbinfo,SQL_OTHER_INDEX)
    v_data.append(['索引(其他)',len(v_results)])
    if v_option=="DETAIL":
        v_other_index = v_results

    #--query view
    SQL_VIEW="""
    select view_name from dba_views where owner='"""+v_analyze_user+"""'
    """
    v_results=query_sql(v_dbinfo,SQL_VIEW)
    v_data.append(['视图',len(v_results)])
    if v_option=="DETAIL":
        v_view = v_results

    #--query trigger
    SQL_TRIGGER="""
    select trigger_name from dba_triggers where owner='"""+v_analyze_user+"""'
    """
    v_results=query_sql(v_dbinfo,SQL_TRIGGER)
    v_data.append(['触发器',len(v_results)])
    if v_option=="DETAIL":
        v_trigger = v_results

    #--query procedure
    SQL_PROCEDURE="""
    select object_name from dba_objects where owner='"""+v_analyze_user+"""' and object_type='PROCEDURE'
    """
    v_results=query_sql(v_dbinfo,SQL_PROCEDURE)
    v_data.append(['存储过程',len(v_results)])
    if v_option=="DETAIL":
        v_procedure = v_results

    #--query function
    SQL_FUNCTION="""
    select object_name from dba_objects where owner='"""+v_analyze_user+"""' and object_type='FUNCTION'
    """
    v_results=query_sql(v_dbinfo,SQL_FUNCTION)
    v_data.append(['函数',len(v_results)])
    if v_option=="DETAIL":
        v_function = v_results

    #--query sequence
    SQL_FUNCTION="""
    select object_name from dba_objects where owner='"""+v_analyze_user+"""' and object_type='SEQUENCE'
    """
    v_results=query_sql(v_dbinfo,SQL_FUNCTION)
    v_data.append(['序列',len(v_results)])
    if v_option=="DETAIL":
        v_sequence = v_results

    #--query synonym
    SQL_SYNONYM="""
    select synonym_name,table_owner,table_name from dba_synonyms where owner='"""+v_analyze_user+"""'
    """
    v_results=query_sql(v_dbinfo,SQL_SYNONYM)
    v_data.append(['同义词',len(v_results)])
    if v_option=="DETAIL":
        v_synonym= v_results

    print_html_table(v_page,['对象类别','数量'],v_data)

    #output object info --detail
    if v_option == "DETAIL":
        v_page << h5('对象详细情况',cl='awr')
        v_page << h6('==表(大表)',cl='awr')
        print_html_table(v_page,['表名'],v_big_table)
        v_page << h6('==表(分区表)',cl='awr')
        print_html_table(v_page,['表名'],v_part_table)
        v_page << h6('==含大对象字段',cl='awr')
        print_html_table(v_page,['表名','字段名'],v_lob_column)
        v_page << h6('==非BTree索引',cl='awr')
        print_html_table(v_page,['表名','索引名','类型'],v_other_index)
        v_page << h6('==视图',cl='awr')
        print_html_table(v_page,['视图'],v_view)
        v_page << h6('==触发器',cl='awr')
        print_html_table(v_page,['触发器'],v_trigger)
        v_page << h6('==存储过程',cl='awr')
        print_html_table(v_page,['存储过程'],v_procedure)
        v_page << h6('==函数',cl='awr')
        print_html_table(v_page,['函数'],v_function)
        v_page << h6('==序列',cl='awr')
        print_html_table(v_page,['序列'],v_sequence)
        v_page << h6('==同义词',cl='awr')
        print_html_table(v_page,['同义词','引用表用户','引用表名'],v_synonym)

    #query dml top 20
    SQL_DML_TOP20="""
    select * from (
    select table_name,inserts,updates,deletes,timestamp 
    from dba_tab_modifications 
    where table_owner='"""+v_analyze_user+"""' 
    order by inserts+updates+deletes desc
    ) where rownum<=20
    """
    v_results=query_sql(v_dbinfo,SQL_DML_TOP20)
    v_page << h5('对象DML次数 TOP 20',cl='awr')
    print_html_table(v_page,['表名','INSERT','UPDATE','DELETE','收集时间'],v_results)

    #query service cost last 24 hour
    SQL_SERVICE_COST="""
    select e.stat_name stat_name,e.value - b.value diff
    from dba_hist_service_stat b, dba_hist_service_stat e
    where b.snap_id = (select min(snap_id) from dba_hist_snapshot s where s.begin_interval_time > sysdate - 24)
     and e.snap_id = (select max(snap_id) from dba_hist_snapshot s where s.begin_interval_time > sysdate - 24)
     and b.instance_number = 1
     and e.instance_number = 1
     and b.dbid = (select dbid from v$database)
     and e.dbid = (select dbid from v$database)
     and b.stat_id = e.stat_id
     and b.service_name_hash = e.service_name_hash
     and b.service_name = e.service_name
     and b.service_name = '"""+v_parameters['service_name']+"""'
    order by 1 
    """
    v_results=query_sql(v_dbinfo,SQL_SERVICE_COST)
    v_page << h5('整体资源消耗(最近24小时)',cl='awr')
    print_html_table(v_page,['指标名称','指标值'],v_results)

    v_page << h5('SQL语句情况',cl='awr')
    #query history sql
    SQL_HIST_SQL="""
    select dbms_lob.substr(sql_text,2000,1) from dba_hist_sqltext where sql_id in 
    (
        select distinct sql_id from dba_hist_sqlstat where parsing_schema_name='"""+v_analyze_user+"""'
    )
    """
    v_results=query_sql(v_dbinfo,SQL_HIST_SQL)
    v_sqls=[]
    for oSQL in v_results:
        v_sqls.append(oSQL[0].lower())
    v_data=[]
    v_data.append(['总SQL数',len(v_sqls)])
    #--count long sql
    iCount=0
    for oSQL in v_sqls:
        if len(oSQL)>int(v_parameters['long_sql_size']):
            iCount=iCount+1
    v_data.append(['超长SQL',iCount])
    #--count (not in,not exist)
    iCount=0
    re_str="not in|exist"
    re_pattern=re.compile(re_str)
    for oSQL in v_sqls:
        if re_pattern.search(oSQL):
            iCount=iCount+1
    v_data.append(['ANTI SQL',iCount])
    #--count (oracle only syntax)
    iCount=0
    re_str="rowid|rownum|decode|partition|rullup|cube|sampling|rank|percentile|ntitle|top|bottom|period|lead|lag"
    re_pattern=re.compile(re_str)
    for oSQL in v_sqls:
        if re_pattern.search(oSQL):
            iCount=iCount+1
    v_data.append(['Oracle Syntax SQL',iCount])
    
    #--count(join table)
    iCount=0
    for oSQL in v_sqls:
         if len(extract_tables(oSQL.replace('$','')))>2:
            iCount=iCount+1
    v_data.append(['Join 3+ Table SQL',iCount])
    
    #--count(subquery)
    iCount=0
    re_str="(\D+select\D+)"
    re_pattern=re.compile(re_str)
    for oSQL in v_sqls:
        if re_pattern.search(oSQL):
            iCount=iCount+1
    v_data.append(['SubQuery SQL',iCount])
    
    print_html_table(v_page,['SQL类别','数量'],v_data)
    #output rule
    v_page << h5('规则说明',cl='awr')
    v_page << li('* 大表判断规则1_物理大小: '+str(v_parameters['table_max_size'])+' M',cl='awr')
    v_page << li('* 大表判断规则2_记录数: '+str(v_parameters['table_row_num']),cl='awr')
    v_page << li('* SQL超长标准: '+str(v_parameters['long_sql_size'])+' 字符',cl='awr')
    v_page << li('* ANTI SQL: 指包含关键字(not in、not exist)的语句',cl='awr')
    v_page << li("* Oracle Syntax SqL: 指包含关键字(rowid、rownum、decode、partition、rullup、cube、sampling、rank、percentile、ntitle、top、bottom、period、lead、lag的语句",cl='awr')
    v_page << li('* Join 3+ Table SQL: 关联3个及3个以上表的语句',cl='awr')
    v_page << li('* SubQuery SQL: 包含子查询的语句',cl='awr')
    v_page.printOut(file=v_rpt_filename)

    print "create oracle report file ... " + v_rpt_filename
