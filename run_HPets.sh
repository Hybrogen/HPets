ProcNumber=`ps aux|grep -w "manage.py runserver 0.0.0.0:8882"|grep -v grep|wc -l`
if [ $ProcNumber -ne 0 ];then
   result=$ProcNumber
else
   result=0
   python3 manage.py runserver 0.0.0.0:8882
fi
# echo ${result}
