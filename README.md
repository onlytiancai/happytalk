## HappyTalk

匿名微博，无需注册即可发言，主要用于吐槽，爆料，发泄，当然发征婚，广告，招聘
啥的也可以啦。

### 启动

gunicorn talk_web:wsgiapp --log-file log.log -b 0.0.0.0:8080

### TODO

todo

- todo: 每个IP最多吐10个槽
- todo: 给每个槽点赞的功能
- todo: 吐槽能自动识别链接，图片和视频
- todo: kill -hup gunicron进程，不保存只重新加载model
- todo: 线程安全考虑
- todo: 增加分享到社交网站的功能
- todo: 滚到页首
- todo：吐槽按钮点了后失效
- todo: 点了按钮后页面很慢，应该加个等待效果，别死等
- todo: 敏感词算法优化用trietree, 把最常见的词提前

done

- done: 敏感词过滤
- done: 显示的时候是0号吐友，发帖后就成5号吐友的问题
- done: 最大吐槽数不能超过100，超过100提示用户稍后再吐
- done: 每个IP最少间隔1分钟才能吐下一个槽
- done: 每个槽不能太长
- done: 每个槽24小时后自动小时
- done: 显示每个槽还剩多久销毁
