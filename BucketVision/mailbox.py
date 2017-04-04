'''
Created on Apr 3, 2017

@author: twilson
'''
from threading import Condition

class Mailbox:
    def __init__(self):
        self.cond = Condition()
        self.avail = False
        self.data = None
        
    def put(self, data):
        self.cond.acquire()
        self.data = data
        self.avail = True
        self.cond.notify()
        self.cond.release()
        
    def get(self):
        self.cond.acquire()
        while not self.avail:
            self.cond.wait()
        data = self.data
        self.avail = False
        self.cond.release()
        return data