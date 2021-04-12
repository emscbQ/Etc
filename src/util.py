from datetime import datetime
import json
import openpyxl
import os
import pyexcel
import pyexcel_xls
import pyexcel_xlsx
import pyexcel_io.writers
import re

from datetime import datetime

from tkinter import filedialog, Tk

import xlrd
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.utils.cell import column_index_from_string, get_column_letter


def get_now():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")



def open_selected_excel_to_list(sheet=0):
    root = Tk()
    root.filename = ""
    while not root.filename:
        root.filename = filedialog.askopenfilename(initialdir=os.path.join(os.path.expanduser("~"), "Desktop"),
                                                   title="Choose your file",
                                                   filetypes=(("All files", "*.*"), ("XLSX files", "*.xlsx"),
                                                              ("XLS files", "*.xls"), ("CSV files", "*.csv")))
        if root.filename:
            break

    print("\n선택한 파일:", root.filename)

    root.withdraw()
    root.destroy()
    path = root.filename
    workbook = xlrd.open_workbook(path, on_demand=True)
    worksheet = workbook.sheet_by_index(sheet)
    data = list()
    for row in range(0, worksheet.nrows):
        one_row = list()
        for col in range(worksheet.ncols):
            if type(worksheet.cell_value(row, col)) == float:
                one_row.append(str(int(worksheet.cell_value(row, col))).strip())
            else:
                one_row.append(str(worksheet.cell_value(row, col)).strip())
        data.append(one_row)
        print(f"{len(data)}개 여는 중", end="\r")

    print(get_now(), f"{os.path.basename(path)} 파일을 리스트로 여는 데 성공했습니다.")

    return data



def xls_to_xlsx(xls_path, xlsx_path):
    pyexcel.save_book_as(file_name=xls_path, dest_file_name=xlsx_path)
