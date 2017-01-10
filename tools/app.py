#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright (C) yanghongshun@gmail.com
#

import os,sys,configparser,getopt
import csv,shutil
from openpyxl import Workbook
from openpyxl import load_workbook
import mysql.connector
from mysql.connector import errorcode

# get custom columns data from data files 

APP_TOOLS_DIRNAME = 'tools'
APP_DATA_DIRNAME = 'data'
APP_RESULT_DIRNAME = 'result'

def usage():
    print('import a directory into mysql table')
    print('-s:database connection setting')
    print('-b:block/section in setting file')
    print('-i:data  data directory')
    print('-o:0 create each table for each file in directory or single file')
    print('-o:1 create one table for every file in directory or single file')
    print('when -o 1 ,must keep fields be same in every file of this data directory ')
    print('-t:when -o 1 need to set -t as table name')
    print('example:')
    print('./app.py -s settings.ini -b import -i ../data/10262016  -o 0')
    print('./app.py -s settings.ini -b import -i ../data/10262016  -o 1 -t tbl0109')

###setting config file ####
def readSettings(settingsVar):
    print("reading settings ini")
    conf=configparser.ConfigParser()
    if 'filePath' not in settingsVar:
        print('settingsVar["filePath"] is empty!')	
        sys.exit()	
    else:
         filePath = settingsVar['filePath']
    if 'section' not in settingsVar:
        print('settingsVar["section"] is empty!')
        sys.exit()
    else:
        section = settingsVar['section']
    #filePath
    if os.path.isfile(filePath):
        conf.read(filePath)
    else:
        print(" %s not exist!" % filePath)	
        sys.exit()
    #section
    if section not in conf.sections():
        print(section + " not exist!")
        sys.exit()
    print("read end")

    return conf[section]
###setting config file end #####
def mysqlConnector(config):
    
    print("connecting remote mysql database ")
    try:
        conn=mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    print("connected successfully")
    return conn
def _getConnection(settings):
    print("connected to remote mysql database online")
    dbConfig = {
        'user':settings['user'],
        'password':settings['password'],
        'host':settings['host'],
        'port':settings['port'],
        'database':settings['database'],
        'raise_on_warnings':True
    }
    cnx = mysqlConnector(dbConfig)
    
    return cnx


def create_table(settings,schema_dict):
    cnx = _getConnection(settings)
    cursor = cnx.cursor()
    schema_dict_mysql=genToMySQLString(schema_dict)
    for name, ddl in schema_dict_mysql.items():
        try:
            print("Creating table: %s " % name)
            cursor.execute(ddl)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("OK")

    cursor.close()
    cnx.close()
    print('closed mysql connection')

def genToMySQLString(schema_dict):
    
    create_field_cmd=""
    for fld in schema_dict['field_name']:
        create_field_cmd+=" `"+fld+"` "+" TEXT DEFAULT NULL,"

    create_table_cmd = " CREATE TABLE `" + schema_dict['table_name']+"` ( "+create_field_cmd.rstrip(",")+" ) "

    table={}
    table[schema_dict['table_name']]=(create_table_cmd)
    return table

def genInsertFieldStr(schema_dict):
    insert_field_cmd=""
    insert_field_cmd_v=""
    for fld in schema_dict['field_name']:
        insert_field_cmd+="`"+fld+"`,"
        insert_field_cmd_v+="%s,"

    insert_table_cmd = "INSERT INTO `"+ schema_dict['table_name']+"` ( "+ insert_field_cmd.rstrip(",")+" ) VALUES ("+insert_field_cmd_v.rstrip(',')+")"
    
    return insert_table_cmd

def insert_data_into_mysql(table_data,settings,schema_dict):
    cnx = _getConnection(settings)
    cursor = cnx.cursor()

    insert_row_ptn = (genInsertFieldStr(schema_dict)) 

    for row in table_data:
        cursor.execute(insert_row_ptn,tuple(row))
        cnx.commit()

    cursor.close()
    cnx.close()
    print('closed mysql connection')

def getDataFromCSV(title,spliter,filePath):
    print("reading data from csv file:%s" % filePath)
    data = []
    if not os.path.isfile(filePath):
        print("%s not exist!" % filePath)
        sys.exit()
    csvfile=csv.reader(open(filePath, 'r'),delimiter=spliter)
    for line in csvfile:
        data.append(line)
    if title == True:
        print("delete first row:title row")
        del data[0]
    print("reading end")
    return data

def saveDataToCSV(title,data,filePath,fmt=''):
    print("saving data to csv file:%s" % filePath)
    if os.path.isfile(filePath):
        print("delete old csv file:%s" % filePath)
        os.remove(filePath)
    file_handle = open(filePath,'w')
    if fmt=='':
        csv_writer = csv.writer(file_handle,delimiter=' ')
    else:
        csv_writer = csv.writer(file_handle,delimiter=fmt)
    if len(title) >0 :
        csv_writer.writerow(title)
    csv_writer.writerows(data)
    file_handle.close()
    print("saved end")

def generateResultFilePath(dataFilePath,prefix=''):
	
    print("generating result file path from data file path:%s" % dataFilePath)
    filename,fileext=os.path.splitext(os.path.basename(dataFilePath))
    if prefix=='':
        resultFileName = 'result_'+filename+'.csv'
    else:
        resultFileName = 'result'+prefix+filename+'.csv'
    dataFileAbsPath = os.path.abspath(dataFilePath)
    app_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))	
    app_data_dir = app_root_dir + os.sep + APP_DATA_DIRNAME+os.sep
    app_result_dir = app_root_dir + os.sep + APP_RESULT_DIRNAME+os.sep
    result_tmp_dirstr = os.path.dirname(dataFileAbsPath).replace(app_data_dir,'')
    resultFileDir = os.path.join(app_result_dir,result_tmp_dirstr)
    if not os.path.exists(resultFileDir):
        print("create directory:%s " % resultFileDir)
        os.makedirs(resultFileDir)
    
    resultFilePath = os.path.join(resultFileDir,resultFileName)
    print("result file path is:%s" % resultFilePath)
    print("generated end")
    return resultFilePath

def getColDataFromFile(dataFilePath,settings):
    _getColDataFromFile(dataFilePath,settings)
	
def _getColDataFromFile(dataFilePath,settings):
    print("acting input   data file")
    _check_fieldname=[]
    _check_fieldname_filename=""
    
    created_tbl=0
   
    inserted_files_num=0
    
    schema_dict={}

    if os.path.isdir(dataFilePath):
        print("  data file is a directory:%s" % dataFilePath)
        for root,dirs,files in os.walk(os.path.abspath(dataFilePath)):
            for file in files:
                filename,fileext=os.path.splitext(file)
                if fileext in ['.csv','.xlsx']:
                    datafileabspath = root+os.sep+file					
                    schema_data=_getColDataFromSingleFile(datafileabspath)  
                    ## just need first file field_name as check
                    ## every file must equal this _check_fieldname
                    if not _check_fieldname:
                        _check_fieldname=schema_data["field_name"]
                        _check_fieldname_filename=filename
                    if settings['option']=='1':
                        if schema_data['field_name'] == _check_fieldname:
                            # only 1 table
                            if created_tbl==0:
                                schema_dict['field_name']=_check_fieldname
                                schema_dict['table_name']=settings['table_name']
                                create_table(settings,schema_dict)
                                created_tbl=1

                            if created_tbl==1:
                                insert_data_into_mysql(schema_data['table_data'],settings,schema_dict)
                                inserted_files_num+=1
                                print('*'*200)
                                print('insert %s into mysql databalse completed' % datafileabspath)
                                print('*'*200)
                        else:
                            print('%s column name is not same with %s' % (filename,_check_fieldname_filename))
                            print('x'*100)
                            print(_check_fieldname_filename)
                            print(_check_fieldname)
                            print('x'*100)
                            print(filename)
                            print(schema_data['field_name'])
                            print('x'*100)
                            sys.exit(1)
                    elif settings['option']=='0':
                        # multi table
                        schema_dict['field_name']=schema_data['field_name']
                        schema_dict['table_name']=schema_data['table_name']
                        create_table(settings,schema_dict)

                        insert_data_into_mysql(schema_data['table_data'],settings,schema_dict)
                        inserted_files_num+=1
                        print('*'*200)
                        print('insert %s into mysql databalse completed' % datafileabspath)
                        print('*'*200)
    print("action is end")
    print('+'*100)
    print('inserted %d file' % inserted_files_num)
    print('+'*100)

def _getColDataFromSingleFile(datafileabspath):
    print("data file :%s" % datafileabspath)
    if not os.path.isfile(datafileabspath):
        print("data file :%s is not exist!" % datafileabspath)
        sys.exit()
    resultFilePath = generateResultFilePath(datafileabspath)
    if os.path.isfile(resultFilePath):
        print("delete old  result file :%s" % resultFilePath)
        os.remove(resultFilePath)
    print("loading file")
    i=0
    filename,fileext=os.path.splitext(datafileabspath)
    if fileext in ['.csv','.xlsx']:
        inputFileDataSetOrig = []
        if fileext=='.csv':
            inputFileDataSetOrig = getDataFromCSV(False,',',datafileabspath)
        elif fileext == '.xlsx':
            wb=load_workbook(filename=datafileabspath,data_only=True,read_only=True)##fast mode
            ws=wb.active
            for row in ws.rows:
                file_row=[]
                for cell in row:
                    file_row.append(cell.value)
                inputFileDataSetOrig.append(file_row)
        
        inputFileDataSetOrigTitleRow = inputFileDataSetOrig[0]
        cols_name=[] 
        for col in inputFileDataSetOrigTitleRow:
            print(i,col)
            new_fld=col.replace(' ','_')
            cols_name.append(new_fld)
            i+=1
    else:
        sys.exit(1)
    table_name=os.path.splitext(os.path.basename(datafileabspath))[0].replace(' ','_')
    field_name=cols_name
    table_data=[]

    field_name.insert(0,'filename')
    for cl in inputFileDataSetOrig[1:]:
       cl.insert(0,table_name)
       table_data.append(cl)

    schema_data={
        'table_name':table_name,
        'field_name':field_name,
        'table_data':table_data
    }
    #saveDataToCSV([],colDataSet,resultFilePath,delimiter)	
    return schema_data

def main():
    try:
        opts,args = getopt.getopt(sys.argv[1:],"hs:b:i:o:t:",["--setting","--block","--input=","--option","--tablename"])
    except getopt.GetoptError as err:
        print(err) 
        usage()
        sys.exit(2)

    input_data=""	
    setting_var = {
        'filePath':"",        
        'section':"" 
    }
    ##when -o 1:just one table
    _tablename=""

    _option=""

    for opt,arg in opts:
        if opt in ('-h',"--help"):
            usage()
            sys.exit()
        elif opt in ('-i','--input'):
            input_data=arg
        elif opt in ('-s','--setting'):
            setting_var['filePath']=arg
        elif opt in ('-b','--block'):
            setting_var['section']=arg
        elif opt in ('-o','--option'):
            _option=arg
        elif opt in ('-t','--tablename'):
            _tablename=arg


    if setting_var['filePath'] !='':
        settings=readSettings(setting_var)
        settings['option']=_option
        if _option=='1':
            if _tablename=="":
                print('please set the only one table name')
                sys.exit(1)

        settings['table_name']=_tablename
        # print(settings['host'])
        #importMySQL(settings,input_data)
        getColDataFromFile(input_data,settings)
    else:
        sys.exit()


if __name__ == "__main__":
    main()
