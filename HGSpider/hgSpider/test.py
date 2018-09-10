import json
import os

import requests
import xlwt

from conf import settings


def generate_excel():
    book = xlwt.Workbook()
    sheet_head = book.add_sheet('表头')
    sheet_head.write(0,0,'哈哈')
    sheet_head.write(0,1,'')
    sheet_head.write(0,2,'1')
    book.save("D:\\123456.xls")

if __name__ == "__main__":
    generate_excel()
