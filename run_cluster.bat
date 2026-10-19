@echo off
TITLE Apache Hadoop, Pig & Hive WSL Cluster
COLOR 0A
echo =======================================================================
echo          APACHE HADOOP, HDFS, YARN, PIG & HIVE CLUSTER
echo          WSL Ubuntu Big Data Environment Launcher
echo =======================================================================
echo.
echo [*] Starting Apache Hadoop HDFS, YARN, Pig & Hive in WSL...
echo.

wsl -d Ubuntu -e bash /mnt/d/projects/Crime_Analytics_BDC/scripts/run_real_hadoop_cluster.sh

echo.
echo =======================================================================
echo [*] Big Data cluster execution completed!
echo =======================================================================
pause
