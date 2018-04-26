# 使用PC/SC读卡器执行批量APDU #
* 使用帮助
*  安装python2.7
*  安装swig
*  安装VC for Python2.7
*  安装pc/sc库 pyscard： pip install pyscard
*  连接pc/sc卡
*  使用方式：
    python testStress.py --input script.txt --output result.txt --log result.log
    --input 输入的APDU脚本文件
    --output  输出的结果文件（执行失败才会记录）
    --log  运行log
    --count 执行循环次数
    --init 初始次数
    --port 端口号
