## HappyTalk

匿名微博，无需注册即可发言，主要用于吐槽，爆料，发泄，当然发征婚，广告，招聘
啥的也可以啦。

### 启动

gunicorn talk_web:wsgiapp --log-file log.log -b 0.0.0.0:8080

### TODO

- todo: 最大吐槽数不能超过100，超过100提示用户稍后再吐
- todo: 每个IP最多吐10个槽
- todo: 每个IP最少间隔1分钟才能吐下一个槽
- todo: 给每个槽点赞的功能
- done: 每个槽不能超过140个字
- todo: 吐槽能自动识别链接，图片和视频
- todo: 每个槽24小时后自动小时
- todo: kill -hup gunicron进程，不保存只重新加载model
