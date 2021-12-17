# Elaina

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/817020a83bed49f9b5be3c150eedfc91)](https://app.codacy.com/gh/wyapx/Elaina?utm_source=github.com&utm_medium=referral&utm_content=wyapx/Elaina&utm_campaign=Badge_Grade_Settings)

一个高性能的mirai sdk（基于mirai-api-http）

## 运行要求

Python 3.8+

Mirai-API-HTTP v2.0+

注：**Mirai-API-HTTP需要启用ws adapter和http adapter**

## 开始使用

```python
from ela.app import Mirai
from ela.message.models import Plain

# 实例化类，以便接下来使用
mirai_app = Mirai("http://%host%:%port%/", qq=1234567890, verify_key="YourVerifyKeyHere")

@mirai_app.register("GroupMessage")  # 将一个函数绑定到一个事件上
async def on_groupmessage(app: Mirai, ev):
    # ev对应每一个事件的返回值
    if str(ev.messageChain) == "Hello":
        await app.sendGroupMessage(ev.group, [Plain("Hi")])
        
if __name__ == '__main__':
    mirai_app.run()
```

