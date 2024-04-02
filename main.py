import mysql.connector
import tkinter as tk
from tkinter import *
from tkinter import filedialog,messagebox, DISABLED, NORMAL
import pandas as pd
import random
import numpy as np
from functools import partial
import os
import sqlalchemy
import pymysql

# GUI PART
root = Tk()
root.title('Teacher Time Table ')
root.geometry("400x300")

def get_teachers():
        mycon=mysql_connector(username,passd,database)
        mycursor=mycon.cursor()
        mycursor.execute('select Tcode, Name from teachers;')
        teachers_data=mycursor.fetchall()
        teachers=[]
        teachers_name=[]
        for a in teachers_data:
            teachers.append('T'+str(a[0]))
            teachers_name.append(a[1])
        return teachers_name, teachers
    

def get_classes():
        mycon=mysql_connector(username,passd,database)
        mycursor=mycon.cursor()
        mycursor.execute('select Class,Section from classes;')
        classes_data=mycursor.fetchall()
        classes_data=pd.DataFrame(classes_data)
        classes=[]
        for a in classes_data.iterrows():
                x='S'+str(a[1].loc[0])+a[1].loc[1]
                classes.append(x)
        return classes
               
        
def assignTeacher(n):
        mycon=mysql_connector(username,passd,database)
        mycursor=mycon.cursor()
        mycursor.execute('select class,section,Scode1,Scode2,Scode3,Scode4,Scode5 from Classes;')
        Class=mycursor.fetchall()
        mycursor.execute('select nsub1,nsub2,nsub3,nsub4,nsub5 from Classes;')
        n_subject=mycursor.fetchall()
        mycursor.execute('select Tcode from teachers;')
        teachers=mycursor.fetchall()
        teacher_nassigned={}
        for i in teachers:
                teacher_nassigned[i[0]]=0
        for sub_req in Class:
                x=0
                subject_count=0
                for i in sub_req[2:]:
                    mycursor.execute(f'select Tcode from Teachers where Scode1="{i}" || Scode2="{i}";')
                    T_available=mycursor.fetchall()
                    for i in T_available:
                            t_choose=random.choice(T_available)
                            if teacher_nassigned[t_choose[0]]+int(n_subject[x][subject_count])<=n*6:
                                mycursor.execute(f'update classes set T{subject_count+1}="{t_choose[0]}" where class="{sub_req[0]}" and section="{sub_req[1]}";')
                                
                                teacher_nassigned[t_choose[0]]+=int(n_subject[x][subject_count])
                                subject_count+=1
                                T_available.remove(t_choose)
                                mycon.commit()
                                break
                mycon.commit()
                x+=1


def timetable(n):
        engine=sqlalchemy.create_engine(f'mysql+pymysql://{username}:{passd}@localhost/{database}')
        df=pd.read_csv('classes_data.csv',)
        classes_column=list(df.columns)
        classes_column.remove('Section')
        dtype_classes={'Section':sqlalchemy.String(10)}
        for i in classes_column:
                dtype_classes[i]=sqlalchemy.INTEGER
                
        df1=pd.read_csv('teachers_data.csv')
        df2=pd.read_csv('scodes.csv')
        df.to_sql('classes',engine,if_exists='replace',index=False,dtype=dtype_classes)
        df1.to_sql('teachers',engine,if_exists='replace',index=False,dtype={'Tcode1':sqlalchemy.INTEGER,'Scode1':sqlalchemy.INTEGER,'Scode2':sqlalchemy.INTEGER})
        df2.to_sql('scodes',engine,if_exists='replace',index=False,dtype={'code':sqlalchemy.INTEGER})
        day_dic=dict(zip(np.arange(6),['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']))
        n_period=[]
        dtype_class={'Day':sqlalchemy.String(10)}
        dtype_teacher={'Day':sqlalchemy.String(10)}
        for i in range(n):
                n_period.append('period'+str(i+1))
                dtype_class['period'+str(i+1)]=sqlalchemy.INTEGER
                dtype_teacher['period'+str(i+1)]=sqlalchemy.String(10)
        teachers_name, teachers=get_teachers()
        dictionary={'Day':['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']}
        
        for a in range(1,1+n):
                dictionary[f'period{a}']=[np.nan for i in range(6)]
        df3=pd.DataFrame(dictionary)
        for i in get_classes():
                df3.to_sql(i.lower(),engine,if_exists='replace',index=False,dtype=dtype_class)
        for i in teachers:
                df3.to_sql(i.lower(),engine,if_exists='replace',index=False,dtype=dtype_teacher)
        assignTeacher(n)
        

        mycon=mysql_connector(username,passd,database)
        mycursor=mycon.cursor()
        
        period_dic=dict(zip(np.arange(n),n_period))
        mycursor.execute('select class,section from classes;')
        classes_data=mycursor.fetchall()
        for classes in classes_data:
                mycursor.execute(f'select T1,T2,T3,T4,T5 from classes where class="{classes[0]}"&& section="{classes[1]}";')
                all_teachers=mycursor.fetchone()
                all_teachers=list(all_teachers)
                print(all_teachers)
                period_list=list(np.arange(6*n))
                Class_tofill=dict(zip(['Nsub1','Nsub2','Nsub3','Nsub4','Nsub5'],[0 for i in range(5)]))
                for i in range(1,len(Class_tofill)+1):
                        mycursor.execute(f'select Scode{i},T{i},Nsub{i} from classes where class="{classes[0]}"&& section="{classes[1]}";')
                        (subject, teacher, numberofperiods)= mycursor.fetchone()
                        other_teacher=all_teachers.copy()
                        other_teacher.remove(teacher)
                        
                        period_checked=period_list.copy()
                        while Class_tofill['Nsub'+str(i)]<numberofperiods:
                                slot=random.choice(period_checked)
                                day=day_dic.get(slot//n)
                                period=period_dic.get(slot%n)
                                mycursor.execute(f'select {period} from T{teacher} where day="{day}";')
                                teacher_free_check=mycursor.fetchone()
                                if teacher_free_check[0]==None:
                                        period_list.remove(slot)
                                        mycursor.execute(f'update s{classes[0]}{classes[1]} set {period}={subject} where Day="{day}"')
                                        mycursor.execute(f'update T{teacher} set {period}="s{classes[0]}{classes[1]}" where Day="{day}"')
                                        print(f'Assigned T{teacher} {period} for s{classes[0]}{classes[1]} at {day}')
                                        Class_tofill['Nsub'+str(i)]+=1
                                        mycon.commit()
                                period_checked.remove(slot)
                             
                                if len(period_checked)==0 and Class_tofill['Nsub'+str(i)]<numberofperiods:
                                        problem_solve = False
                                        for Try in range(6*n):#for every possible position
                                                trialday=day_dic.get(Try//n)
                                                trialperiod=period_dic.get(Try%n)
                                                mycursor.execute(f'select {trialperiod} from T{teacher} where day="{trialday}";')
                                                trial=mycursor.fetchone()
                                              
                                                if trial[0]==None:# Teacher is free
                                                       
                                                        for t in other_teacher:
                                                                mycursor.execute(f'select {trialperiod} from T{t} where day="{trialday}";')
                                                                otherTrial=mycursor.fetchone()
                                                                
                                                                if otherTrial[0]== 's'+str(classes[0])+classes[1]:#other teacher teaches same class
                                                                        #Get for a slot for other teacher
                                                                        
                                                                        for a in period_list:
                                                                                
                                                                                #Check other teacher is free
                                                                                otherday=day_dic.get(a//n)
                                                                                otherperiod=period_dic.get(a%n)
                                                                                mycursor.execute(f'select {otherperiod} from T{t} where day="{otherday}";')
                                                                                check_t=mycursor.fetchone()
                                                                                if check_t[0]==None:
                                                                                        
                                                                                        mycursor.execute(f'select {trialperiod} from {otherTrial[0]} where day="{trialday}";')
                                                                                        s=mycursor.fetchone()
                                                                                        # other trial is class
                                                                                        mycursor.execute(f'update {otherTrial[0]} set {trialperiod}={subject} where day="{trialday}";')
                                                                                        mycursor.execute(f'update t{t} set {trialperiod}=Null where day="{trialday}";')
                                                                                        mycursor.execute(f'update t{t} set {otherperiod}="{otherTrial[0]}" where day="{otherday}";')
                                                                                        mycursor.execute(f'update {otherTrial[0]} set {otherperiod}={s[0]} where day="{otherday}";')
                                                                                        mycursor.execute(f'update T{teacher} set {trialperiod}="s{classes[0]}{classes[1]}" where Day="{trialday}";')
                                                                                        Class_tofill['Nsub'+str(i)]+=1
                                                                                        mycon.commit()
                                                                                        period_list.remove(a)
                                                                                        period_checked=period_list.copy()
                                                                
                                                                                        problem_solve=True
                                                                                        if problem_solve:
                                                                                                break
                
                                                                
                                                                if problem_solve:
                                                                        break
                                                if problem_solve:
                                                        break
               
                                                        mycursor.execute(f'select t1,t2,t3,t4,t5 from classes where class={trial[0][1:-2]}, section="{trial[-1]}";')
                                                        other_class_teachers=mycursor.fetchall()
                                                        other_class_teachers=list(other_class_teachers)
                                                        
                                                        other_class_teachers=other_class_teachers.remove(teacher)
                                                        for other_classes_teacher_list in other_class_teachers:
                                                                for other_teacher in other_classes_teacher_list:
                                                                        
                                                         
                                                                        for one in period_list:#one is wher i want teacher = trial = class
                                                                                oneday=day_dic.get(one//n)
                                                                                oneperiod=period_dic.get(one%n)
                                                                                mycursor.execute('select {oneperiod} from t{other_teacher} where day="{oneday}";')
                                                                                
                                                                                other_teacher_state=mycursor.fetchone()
                                                                                
                                                                                mycursor.execute('select {trialperiod} from t{other_teacher} where day="{trialday}";')
                                                                                other_teacher_state_at_trial=mycursor.fetchone()
                                                                                mycursor.execute('select {oneperiod} from t{other_teacher} where day="{oneday}";')
                                                                                teacher_state=mycursor.fetchone()
                                                                                if other_teacher_state[0]==None and other_teacher_state_at_trial[0]==teacher_state[0]:
                
                                                                                        #change both suject in both class
                                                                                        #change both teacher both class
                                                                                        mycursor.execute(f'update t{other_teacher} set {oneperiod}="{teacher_state[0]}" where day="{oneday}";')
                                                                                        mycursor.execute(f'update t{other_teacher} set {trialperiod}=Null where day="{trialday}";')
                                                                                        mycursor.execute(f'update t{teacher} set {oneperiod}="s{classes[0]}{classes[1]}" where day="{oneday}";')
                                                                                        mycursor.execute(f'update t{teacher} set {trialperiod}="{teacher_state}" where day="{trialday}";')
                                                                                        mycursor.execute(f'select {oneperiod} from {teacher_state} where day="{oneday}"')
                                                                                        subject1=mycursor.fetchone()
                                                                                        mycursor.execute(f'select {trialperiod} from {teacher_state} where day="{trialday}"')
                                                                                        subject2=mycursor.fetchone()
                                                                                        mycursor.execute(f'update {teacher_state} set {oneperiod}={subject2} where day="{oneday}";')
                                                                                        mycursor.execute(f'update {teacher_state} set {trialperiod}={subject1} where day="{trialday}";')
                                                                                        mycursor.execute(f'update {classes[0]}{classes[1]} set {oneperiod}=subect where day="{oneday}";')
                                                                                        Class_tofill['Nsub'+str(i)]+=1
                                                                                        period_list.remove(one)
                                                                                        period_checked=period_list.copy()
                                                                                        
                                                                                        mycon.commit()
                                                                                        problem_solve=True
                                                                                if problem_solve:
                                                                                        break
                                                                        if problem_solve:
                                                                                break
                                                                if problem_solve:
                                                                        break
     
def com1():
        top = Toplevel()
        top.title("Teachers' time table")
        mycon=mysql_connector(username,passd,database)
        mycursor=mycon.cursor()
        def view_teacher(a,b):
                column=2
                for p in ['Day','Period1','Period2','Period3','Period4','Period5','Period6','Period7']:
                        l=Label(top, text=p ).grid(column=column, row=1)
                        column+=1
                l=Label(top, text=b, width=100).grid(row=0,column=1,columnspan=9)
                mycon=mysql_connector(username,passd,database)
                mycursor=mycon.cursor()
                mycursor.execute(f'select*from t{a}')
                row=2
                for i in mycursor.fetchall():
                        column=2
                        for j in i:
                                lab=Label(top, text=j, width=10).grid(row=row,column=column)
                                column+=1
                        row+=1
        row_count=1
        mycursor.execute('select Tcode,Name from teachers;')
        for (a,b) in mycursor.fetchall():
                command=partial(view_teacher,a,b)
                button=Button(top, width=20, text=b, command = command).grid(row=row_count, column=0)
                row_count+=1

                                 
def com2():
        top = Toplevel()
        top.title("Classes time table")
        mycon=mysql_connector(username,passd,database)
        mycursor=mycon.cursor()
        classes= get_classes()
        def view_classes(c):
                column=2
                for p in ['Day','Period1','Period2','Period3','Period4','Period5','Period6','Period7']:
                        l=Label(top, text=p ).grid(column=column, row=1)
                        column+=1
                label=Label(top, text=c, width=40).grid(row=0,column=1,columnspan=5)
                mycon=mysql_connector(username,passd,database)
                mycursor=mycon.cursor()
                row_count=1
                mycursor.execute(f'select*from {c}')
                row=2
                for i in mycursor.fetchall():
                        column=2
                        for j in i:
                                if str(j).isnumeric():
                                        mycursor.execute(f'select subject from scodes where code={j}')
                                        j=mycursor.fetchone()
                                lab=Label(top, text=j, width=18).grid(row=row,column=column)
                                column+=1
                        row+=1
        row_count=0
        for c in classes:
                command=partial(view_classes,c)
                button=Button(top, width=20, text=c.lstrip('s'), command = command).grid(row=row_count, column=0)
                row_count+=1
                        
                                

        
def com3():
        top = Toplevel()
        top.title("New Time Table")
        l=Label(top,text='Enter number of periods').pack()
        e=Entry(top, width=25,textvariable=tk.StringVar())
        e.pack()
        def get():
                n=e.get() 
                n=int(n)
                timetable(n)
        b=Button(top , width=25, text='Submit', command=get).pack()
        
        
def com4():
        top = Toplevel()
        top.title("Substitution")
        mycon=mysql_connector(username,passd,database)
        mycursor=mycon.cursor()
        mycursor.execute('select month(now()), day(date(now())),monthname(now()),year(now()), dayofweek(date(now()));')
        data=mycursor.fetchall()
        [(month,day_today,month,year,dayofweek)]=data
        df=pd.read_csv(month+str(year)+'.csv',usecols=[0,1])
        teacher_dic=dict(zip(df.loc[:,'0'],df.loc[:,'1']))
        column_name=f'{year}-{month}-{day_today}'
        df1=pd.read_csv(month+str(year)+'.csv',usecols=[column_name])
        
        day_dic=dict(zip(np.arange(2,8),['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']))
        dayofweek=day_dic[dayofweek]
        absent_teachers=[]
        present_teachers=[]
        x=0
        if df1[column_name].isnull().any():
                messagebox.showwarning('Attendence Empty','Enter teachers attendence')
                top.destroy()
        else:
                for i in df.iterrows():
                        if (df1.loc[x,column_name]=='a' or df1.loc[x,column_name]=='A'):
                                absent_teachers.append(df.loc[x,'0'])
                        elif (df1.loc[x,column_name]=='p' or df1.loc[x,column_name]=='P'):
                                present_teachers.append(df.loc[x,'0'])
                        x+=1
                if len(absent_teachers)==0:
                        messagebox.showinfo('All Teachers Present','All Teachers are Present \n No Arrangement')
                        top.destroy()
                elif len(present_teachers)<len(get_classes()):
                        messagebox.showwarning('Unable to make substitution','Number of teachers present are less')
                        top.destroy()
                else:
                        l=Label(top, text=' ').grid(row=0,column=0)
                        column=1
                        for p in ['Period1','Period2','Period3','Period4','Period5','Period6','Period7']:
                                l=Label(top, text=p ).grid(column=column, row=1)
                                row=2
                                present=present_teachers.copy()
                                for i in absent_teachers:
                                    mycursor.execute(f'select {p} from {i} where day="{dayofweek}";')
                                    Class=mycursor.fetchone()
                                    solve = False
                                    if Class[0]!=None:
                                        while not solve:
                                            t_choose=random.choice(present)
                                            mycursor.execute(f'select {p} from {t_choose} where day="{dayofweek}";' )
                                            r=mycursor.fetchone()
                                            if r[0]== None:
                                                solve=True
                                                l=Label(top, text=teacher_dic[t_choose]+'\n'+Class[0].lstrip('s'),width=20 ).grid(column=column, row=row)
                                                present.remove(t_choose)
                                        row+=1
                                column+=1
                        l=Label(top, text=' ').grid(row=0, column=0)
                        
                
def com5():
        mycon=mysql_connector(username,passd,database)
        mycursor=mycon.cursor()
        mycursor.execute('select month(now()), day(last_day(now())),day(date(now())),monthname(now()),year(now());')
        data = mycursor.fetchall()
        [(month,last_day,day_today,month,year)]=data
        filename=month+str(year)+'.csv'
        try:
                f=open(filename,'r')
                path=os.path.abspath(filename)
                messagebox.showwarning('File already Exist',f'File already Exist as \n{path}')
        except:
                teachers_name,teachers = get_teachers()
                columns=[0,1]
                for i in range(1,int(last_day)+1):
                        columns.append(f'{year}-{month}-{i}')
                df=pd.DataFrame([],columns=columns)
                df.loc[:,0]=teachers
                df.loc[:,1]=teachers_name
                df.to_csv(month+str(year)+'.csv',index=False)
                path=os.path.abspath(filename)
                messagebox.showinfo('File Created',f'File Created as \n{path}')
def work():
        frame = LabelFrame(root).grid()
        state=NORMAL
        try:
                mycon=mysql.connector.connect(host='localhost',user=username,password=passd,database=database)
                mycursor=mycon.cursor()
                mycursor.execute('show tables;')
                tables=mycursor.fetchall()
                if ('classes',)in tables and ('teachers',) in tables and ('scodes',) in tables:
                        pass
                else :
                        state=DISABLED   
        except:
                state=DISABLED
                mycon=mysql.connector.connect(host='localhost',user=username,password=passd,)
                mycursor=mycon.cursor()
                mycursor.execute(f'create database {database}')
                mycon.commit()                
        b1=Button(frame, text="View Teachers' time table",state=state, width=20, command=com1).grid(row=7,column=0)
        b2=Button(frame, text="View Classes time table", state=state, width=20,command=com2).grid(row=6,column=0)
        b3=Button(frame, text="Create New Time Table", width=20, command=com3).grid(row=7,column=1)
        b4=Button(frame, text="Create Substitution",state=state, width=20, command=com4).grid(row=6,column=1)
        b4=Button(frame, text="Create Attendence Sheet", state=state,width=20, command=com5).grid(row=8,column=1)
def mysql_connector(username,passd,database):
        mycon=mysql.connector.connect(host='localhost',user=username,password=passd,database=database)
        return mycon
        
def checkMysqlPassword():
        global username
        #username='root'
        username=e_username.get()
        global passd
        #passd='root'
        passd=e_password.get()
        global database
        #database='vibhord'
        database=e_database.get()
        try :
                mycon=mysql.connector.connect(host='localhost',user=username,password=passd)
                mycursor=mycon.cursor()
        except:
                Err=Label(root, text='Unable to connect to mysql').grid()
        if mycon.is_connected():
                work()
                
info = Label(root, text='Enter your mysql username and password').grid(row=0,column=0, columnspan=2)
usern = Label(root, text='Enter Username',width=30).grid(row=1,column=0)
passw = Label(root, text='Enter Password').grid(row=2,column=0)
databse = Label(root, text='Enter Database').grid(row=3,column=0)
e_username = Entry(root, width=25,textvariable=tk.StringVar())
e_password = Entry(root, width=25,textvariable=tk.StringVar(), show='*')
e_database = Entry(root, width=25,textvariable=tk.StringVar())
e_username.grid(row=1,column=1)
e_password.grid(row=2,column=1)
e_database.grid(row=3,column=1)
get_button = Button(root, text='Submit',command= checkMysqlPassword).grid(row=4, column=0, columnspan=2)
space= Label(root, text='           ').grid(row=5,columnspan=2)
root.mainloop()



                                

                
                
