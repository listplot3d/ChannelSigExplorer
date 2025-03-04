
v2025.03.04
* 修改了TGMA的采集数据格式直接为电压值，这样存出来的edf才能直接读

v2025.02.10
* 移除了没使用的import
* 添加与测试了requirements.txt
* 添加了如何写指标的英文说明图
* 修改保存EDF出错的问题
* 录制了tutorial的视频

v2025.02.09
* 注释改成了英文的
* 增加了tutorials文档

v2025.02.04
* 去掉了__Data_IO_Utils.py里面对数据的复制。直接传指针
* tools里面增加了命令行录制edf的功能。
* 实现了界面上按钮录制成edf+

v2025.02.01
* 重构了Bands的数据结构，更简洁了
* 实现了只显示beta波比例的指标
* 将epoch的命名改成了interval,避免与EEG的epoch歧义
* 让“录制”按钮直接调用Lab Recorder的exe

v2025.01.31
* 实现了小波变换的图
* 增加了“录制”按钮，功能还没通

v2025.01.30
* 改进了BaseIndicator中生成模拟信号的方式，增加了随机性
* 多带宽的堆积图可以用了

v2025.01.28
* 在Indicator_Global_Cfg中添加了说明为什么这么实现的注释

v2025.01.27
* 把epoch data的pop操作放到了BaseIndicator.这样写具体指标时，不会忘了删除epoch
* 支持了TGMA设备

v2025.01.26
* 把baseindicator的rawdata的数据结构改为2d的。每个epoch为一行.解决了性能问题，以及简洁了代码

v2025.01.25
* 对脑波频段折线指标进行了重构，band5,band8的切换在代码中只需要一行。
* 解决了频段折线图中，显示跳跃的问题

v2025.01.24
* 从main_window里面再拆出来了GUIComp_Utils.py. 
* 通过文件命名中的__来标记“非指标”，从而在文件浏览器中能够只显示指标
* EmbedSleepNet的softmax显示图上，通过颜色显示判定的stage
* 对通用的指标初始化接口进行了重构，以indicator_update_interval(即epoch时长)作为核心参数

v2025.01.23
* EmbedSleepNet能正常显示softmax的5个灰度值了
* 重构了main_window,把流管理的部分拆出来成单独的文件

v2025.01.22
* 现在指标可以写在子文件夹里了
* EmbedSleepNet的模型能实时调用，并显示在指标浏览器上，数据流打通了。不过显示的内容还要调试。

v2025.01.14
* 实现了8个脑波波段的曲线显示指标

v2025.01.13
* 每次加载指标右侧都新建一个绘图区。以前是每次挤在现有绘图区底下
* 文件浏览器支持双击加载,双击关闭

v2025.01.12
实现了基本的功能：
        muse头环/mne player------>mne-lsl流-------->指标浏览器/运行单独指标文件------->pyqtgraph的显示



TODO:




【低优先级】
* 如何设计，方便指标调用其他指标的输出？ 
  目前都能访问公共绘图区，起码在mainwindow上，数据是通的。
  main_window上面有所有加载的指标的instance列表。通过那个列表可以访问。

* refactor: 用neurokit2的nk.eeg_simulate()来生成模拟信号
  它最自动下载很大的MNE数据，得处理这个问题

* EmbedSleepNet指标的性能优化：pipdub来去掉对scipy.signal的resample的使用
* EmbedSleepNet指标的性能优化：ONNX转换来去掉对pytorch的引用和model.py的引用

* 支持直连TGMA的设备，不经过LSL
  因为本机已经读出来了，没必要经过LSL。本来512hz的就搞得有点卡。但是这事情也不急，TGMA支持
  brainflow之后就自动好实现了

【问题超越了】
* 重构main_window代码，不然太长了LLM处理不完
（不需要重构了，因为通过文件命名中的__来标记“非指标”，main_window不用动了)

* player的数据不显示的问题 - 用mne-lsl viewer检查一下，数据流本身是不是对的

* 贝塔波的比例图 x0.5d
  就是多带宽堆积图中的一个输出，拿出来就行了