from common.logger import logger


class CleanupManager:
    """
    测试数据清理器。
    用例中创建了文章、订单、用户等资源后，可以注册清理动作。
    用例结束后自动倒序清理。
    """

    def __init__(self):
        self._tasks = []

    def add(self, func, *args, **kwargs):
        self._tasks.append((func, args, kwargs))

    def run(self):
        while self._tasks:
            func, args, kwargs = self._tasks.pop()

            try:
                func(*args, **kwargs)
                logger.info(f"测试数据清理成功：{func.__name__}")
            except Exception as e:
                logger.warning(f"测试数据清理失败：{func.__name__}，原因：{e}")
