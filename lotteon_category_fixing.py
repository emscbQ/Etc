from copy import deepcopy

import openpyxl
from openpyxl.utils.cell import column_index_from_string

from src.lotteon_category import LotteonCategory
from src.util import open_selected_excel_to_list

lotteon = LotteonCategory()

category_infos = lotteon.category_command()
can_use_categories = list(filter(lambda category: category[6], category_infos))[1:]

f = open_selected_excel_to_list()

use_YN_col = "I"
u = column_index_from_string(use_YN_col) - 1
modified_rows = [f[0]]
print()

for rn, row in enumerate(f):
    if row[u] == "0":  # False
        row_num = rn + 1
        modified_rows.append(deepcopy(row))
        category_words = [row[4], row[5], row[6], row[7]]
        while True:
            try:
                category_words.remove("")
            except ValueError:
                break
        search_word = category_words[-1]
        searched_words = list(filter(lambda category: category[5].find(search_word) != -1, can_use_categories))
        print(f'"{">".join(category_words)}"을 뭘로 변경하시겠습니까?\n')
        for n, category_info in enumerate(searched_words):
            print(f"{n + 1}. {category_info[5]}")
        selected_n: int = int(input("선택해주세요 >>> ")) - 1
        print()
        f[rn][2] = searched_words[selected_n][4]
        f[rn][3] = searched_words[selected_n][4]
        f[rn][4], f[rn][5], f[rn][6], f[rn][7] = category_words + [""] * (4 - len(category_words))
        f[rn][8] = "MODIFIED"
        modified_rows.append(f[rn])
        modified_rows.append([])

D_wb = openpyxl.Workbook()
D = D_wb.worksheets[0]
D_wb.create_sheet("MODIFIED")
D_modified = D_wb.worksheets[1]
for n, row in enumerate(f):
    D.append(row)
    print(f"진행 중 ({n + 1}/{len(f)})", end="\r")
print("카테고리 시트 완료!")

for n, row in enumerate(modified_rows):
    D_modified.append(row)
    print(f"진행 중 ({n + 1}/{len(modified_rows)})", end="\r")
print("바뀐 열 정보 시트 완료!")

print("엑셀 파일 저장 중...", end="\r")
D_wb.save("lotteon_category_mapping_modified.xlsx")
print("엑셀 파일 저장 완료!")
input("끝!")
