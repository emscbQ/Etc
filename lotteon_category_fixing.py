from copy import deepcopy
from functools import reduce

import openpyxl
from openpyxl.utils.cell import column_index_from_string

from src.lotteon_category import LotteonCategory
from src.util import open_selected_excel_to_list


def _search_words(full_category_name: str, categories: list) -> list:
    word1, word2 = full_category_name.split(">")[-2:]

    search_word = word2
    while True:
        searched_words = list(filter(lambda category: category[5].find(search_word) != -1, categories))
        if len(searched_words) == 0:
            search_candidates = [word2[j:j + i] for i in range(2, len(word2)) for j in range(0, len(word2) - i + 1)]
            all_searched_categories = reduce(lambda a, b: a + b,
                                             [list(filter(lambda category: category[5].find(candidate) != -1, categories)) for
                                              candidate
                                              in search_candidates], list())
            all_searched_categories = sorted(all_searched_categories, key=lambda x: x[4])
            all_searched_categories = reduce(lambda a, b: a + [b] if b not in a else a, all_searched_categories, list())

            if len(all_searched_categories) == 0:
                if search_word == word1:
                    return []
                search_word = word1
                continue
            return all_searched_categories
        else:
            return searched_words


if __name__ == '__main__':

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
            searched_words = _search_words(row[0], can_use_categories)
            if not searched_words:
                print("검색된 카테고리가 없습니다.\n")
                continue
            print()
            for n, category_info in enumerate(searched_words):
                print(f"{n + 1}. {category_info[5]}")
            print(f'\n"{row[0]}"을 뭘로 변경하시겠습니까?\n')
            try:
                selected_n = input("\n선택해주세요 (그만하려면 q, 보기 중에 없으면 x) >>> ")
                if selected_n.lower() == "q":
                    print("이제껏 진행된 사항을 저장합니다.")
                    break
                elif selected_n.lower() == "x":
                    print("다음으로 넘어갑니다.\n")
                    continue
                selected_n = int(selected_n) - 1
            except ValueError:
                print("이제껏 진행된 사항을 저장합니다.")
                break
            print()
            modified_rows.append(deepcopy(row))
            f[rn][2] = searched_words[selected_n][4]
            f[rn][3] = searched_words[selected_n][4]
            f[rn][4], f[rn][5], f[rn][6], f[rn][7] = searched_words[selected_n][0:4]
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
