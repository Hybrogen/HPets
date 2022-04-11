#-*- coding:utf-8 -*-

import os
import json

class CONFIG(object):
    def __init__(self, oriFile: str = None, setFile: str = None, initData: dict = None):
        r"""
        Arguments:
        oriFile -- 原配置文件路径（字符串 str），配置文件最终保存到这个文件中
        setFile -- 重置配置文件路径（字符串 str），此文件会被用户手动修改，通常读取后会被删除
        initData -- 初始化数据（字典 dict 默认为 dict()），当系统刚刚运行的时候，如果原配置文件不存在则创建配置文件并写入初始配置数据
        """
        self.oriFile = oriFile
        self.setFile = setFile
        self.data = initData if initData else dict()
        self.load()

    def check_ori(self) -> bool:
        if not self.oriFile: return False
        return os.path.isfile(self.oriFile)

    def check_set(self) -> bool:
        if not self.setFile: return False
        return os.path.isfile(self.setFile)

    def reset(self) -> bool:
        r"""
        此方法判断是否有【重置文件】，如果有则更新【源文件】和【配置数据】
        """
        if not self.setFile: return False
        resetFlag = False
        if self.check_set():
            os.rename(self.setFile, self.oriFile)
            resetFlag = True
        self.load()
        return resetFlag

    def load(self):
        r"""
        此方法用于加载配置文件中的配置数据，并更新到内存（类成员变量）中
        """
        if not self.oriFile: return
        if not self.check_ori():
            self.save()
        with open(self.oriFile, encoding='utf8') as f:
            try:
                self.data = json.loads(f.readline())
            except json.decoder.JSONDecodeError:
                self.data = dict()

    def save(self):
        r"""
        此方法用于把内存中的配置文件保存到文件中离线
        """
        if not self.oriFile: return
        with open(self.oriFile, 'w', encoding='utf8') as f:
            f.write(json.dumps(self.data))

    def get_data(self, queryFields: list = []):
        r"""
        此方法用于返回内存中的配置数据

        Arguments:
        queryFields -- 请求的字段，按照层级顺序获取

        Return value / exceptions raised:
        - 返回一个字典 dict 内容为内存中的数据
        """
        rdata = self.data
        for f in queryFields: rdata = rdata[f]
        return rdata

    def updata(self, field, data):
        r"""
        此方法用于更新字段
        - 如果数据不需要更新，则直接返回
        - 如果需要更新，则更新后保存到文件离线配置
        """
        if self.data.get(field, None) == data: return
        self.data[field] = data
        self.save()

if __name__ == '__main__':
    conf = CONFIG()

