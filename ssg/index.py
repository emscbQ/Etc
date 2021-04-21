import json
import re
import traceback

import requests

from auth import header, urls
from src.util import get_now, open_selected_excel_to_list

if __name__ == "__main__":
    print("SSG 상품 품절 (출고 지연)")
    log_list = list()
    log_list.append(f"{get_now()} 프로그램 시작")

    try:
        # NOTE Get excel
        print("정보통에서 추출한 엑셀 파일을 선택해주세요.")
        log_list.append(f"{get_now()} 엑셀 읽기 시작")
        excel_data = open_selected_excel_to_list()
        log_list.append(f"{get_now()} 엑셀 읽기 완료")
        order_id_col = excel_data[0].index("판매사이트주문번호")
        product_name_col = excel_data[0].index("상품명")

        order_name_dict = dict()
        for row in excel_data[1:]:
            order_id = row[order_id_col].split()[0]
            try:
                product_name = re.search(r"\[\w+]\s(?P<name>.*)", row[product_name_col]).groupdict().get("name")
            except AttributeError:
                print("상품명이 패턴에 맞지 않습니다. ([ㅇㅇㅇ몰] 상품명)")
                log_list.append(f"{get_now()} 상품명이 패턴에 맞지 않습니다. ({row[product_name_col]})")
                continue
            if order_id in order_name_dict:
                order_name_dict[order_id].append(product_name)
            else:
                order_name_dict[order_id] = [product_name]

        # NOTE 조회 및 출고 지연 등록
        for order in order_name_dict:
            body = dict(
                requestWarehouseOut=dict(
                    commType="01",
                    commValue=order,
                )
            )
            log_list.append(f"{get_now()} {order} 조회 시작")
            response = requests.post(url=urls.get("post_list_warehouse_out"), headers=header, data=json.dumps(body))
            if response.status_code == 200:
                log_list.append(f"{get_now()} {order} 조회 성공")
                rsp = response.json()
                if rsp["result"]["warehouseOuts"][0] == "":
                    print(f"주문 번호로 조회된 출고 지연 등록 가능한 상품이 없습니다. ({order})")
                    log_list.append(f"{get_now()} 주문 번호로 조회된 출고 지연 등록 가능한 상품이 없습니다. ({order})")
                    continue
                for warehouse_out_dict in rsp["result"]["warehouseOuts"]:
                    log_list.append(f"{get_now()} {len(rsp['result']['warehouseOuts'])}개 조회 완료")
                    warehouse_out = warehouse_out_dict["warehouseOut"]
                    if warehouse_out.get("itemNm") in order_name_dict[order]:
                        # 출고지연처리
                        delay_body = dict(
                            requestNoSellRequestRegist=dict(
                                shppNo=warehouse_out.get("shppNo"),  # 배송번호
                                scEvnt="I",  # 등록(I)/삭제(D)
                                shppSeq=warehouse_out.get("shppSeq"),  # 배송순번
                                shortgRsnCd="09",  # 등록/삭제 구분 / 09: 결품, 품절(재고부족)
                                shortgProcDtlc="품절",  # 판매불가사유내용
                                itemId=warehouse_out.get("itemId"),  # 상품번호
                            )
                        )
                        delay_response = requests.post(url=urls.get("post_no_sell_request"), headers=header,
                                                       data=json.dumps(delay_body))
                        if delay_response.status_code == 200:
                            if delay_response.json()["result"]["resultMessage"] == "SUCCESS":
                                print("출고 지연 등록 성공")
                                log_list.append(
                                    f"{get_now()} {warehouse_out.get('shppNo')} / {warehouse_out.get('itemId')} 출고 지연 등록 완료")
                            else:
                                print("출고 지연 등록 실패")
                                log_list.append(
                                    f"{get_now()} {warehouse_out.get('shppNo')} / {warehouse_out.get('itemId')} 출고 지연 등록 실패")
                        else:
                            print("출고 지연 등록 실패")
                            log_list.append(
                                f"{get_now()} {warehouse_out.get('warehouseOut').get('shppNo')} / {warehouse_out.get('warehouseOut').get('itemId')} 출고 지연 등록 실패")
            else:
                print("주문번호로 출고 상품 조회에 실패했습니다.")
                log_list.append(f"{get_now()} {order} 조회 실패")
    except Exception as e:
        print(e.__str__())
        print(traceback.format_exc())
    finally:
        # NOTE 마무리
        with open(f"./logs_{get_now(str_format='%Y-%m-%d')}.txt", "a") as t:
            for line in log_list:
                t.write(f"{line}\n")
        input("엔터를 입력하면 종료됩니다.")
