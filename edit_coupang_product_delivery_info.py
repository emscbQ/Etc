import datetime as dt
import json
import time
from multiprocessing import Process
from urllib import parse

import requests

from coupang_accounts import accounts
from src.coupang_auth import get_header
from src.util import get_now


class CoupangEdit:
    def __init__(self, data: dict):
        self.request = requests.Session()
        self.coupang_api: str = "https://api-gateway.coupang.com"
        self._urls = dict(
            get_products_by_page="/v2/providers/seller_api/apis/api/v1/marketplace/seller-products",
            get_product_info="/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{}",
            returnShipping="/v2/providers/openapi/apis/api/v4/vendors/{}/returnShippingCenters",
            outboundShipping="/v2/providers/marketplace_openapi/apis/api/v1/vendor/shipping-place/outbound",
            edit_product="/v2/providers/seller_api/apis/api/v1/marketplace/seller-products",
            product_type_info="/v2/providers/seller_api/apis/api/v1/marketplace/meta/category-related-metas/display-category-codes/{}",
        )
        self.account_common_info = None
        if not (data.get("partner_no") and data.get("access_key") and data.get("secret_key")):
            raise ValueError("[SECTION]ACCOUNT_INFO 가 비어있습니다.")
        else:
            self.account_common_info = data

        # NOTE 반품지 조회
        self.return_info = dict()
        url = self._urls.get("returnShipping").format(self.account_common_info.get("partner_no"))
        header = get_header(url=url, data=self.account_common_info)
        response = self.request.get(self.coupang_api + url, headers=header, timeout=20)

        if response.status_code != 200:
            raise ValueError("상품 반송 정보 실패")
        return_centers = response.json()["data"]["content"]
        for center in return_centers:
            if center.get("usable") is True and "(API)" in center.get("shippingPlaceName"):
                return_center_info = center
                self.return_info["returnCenterCode"] = return_center_info["returnCenterCode"]
                self.return_info["returnChargeName"] = return_center_info["shippingPlaceName"]
                self.return_info["companyContactNumber"] = return_center_info["placeAddresses"][0][
                    "companyContactNumber"]
                self.return_info["returnZipCode"] = return_center_info["placeAddresses"][0]["returnZipCode"]
                self.return_info["returnAddress"] = return_center_info["placeAddresses"][0]["returnAddress"]
                self.return_info["returnAddressDetail"] = return_center_info["placeAddresses"][0]["returnAddressDetail"]
                break
        if self.return_info.get("returnCenterCode") is None:
            raise ValueError("반품지 정보 등록 필요 (전략팀 문의)")

        # NOTE 출고지 조회
        self.outbound_info = dict()
        params = {
            'searchType': 'FULL',
            'pageNum': 1,
            'pageSize': 50
        }
        query = parse.urlencode(params)

        url = self._urls.get('outboundShipping')
        header = get_header(url=url, data=self.account_common_info, query=query)

        response = self.request.get(self.coupang_api + url, params=params, headers=header, timeout=20)
        if response.status_code != 200:
            raise ValueError("상품 반품지 정보 실패")

        outbound_places = response.json()['content']
        for place in outbound_places:
            if place.get("usable") is True and "(API)" in place.get("shippingPlaceName"):
                self.outbound_info["outboundShippingPlaceCode"] = place["outboundShippingPlaceCode"]
                break
        if self.outbound_info["outboundShippingPlaceCode"] is None:
            raise ValueError("출고지 정보 등록 필요 (전략팀 문의)")

    def renew_return_info(self):
        start_date = dt.datetime.fromisoformat("2015-01-01")
        end_date = dt.datetime.fromisoformat("2021-03-13")  # 이거 전 날까지 실행됨 (0313으로)

        c_date = start_date
        while True:
            try:
                self.edit_product(c_date.strftime("%Y-%m-%d"))
                c_date += dt.timedelta(days=1)
                if c_date == end_date:
                    break
            except Exception as e:
                raise

    def edit_product(self, created_at):
        logs = list()
        in_review_products = list()
        account_name = self.account_common_info.get("name")
        # print(f"Created at : {created_at}")
        logs.append(f"상품 조회 날짜 : {created_at}")
        failure_products = list()
        next_token = 1
        page_count = 1
        while True:
            try:
                # print(f"{get_now()} {account_name} {100 * page_count}개 시작")
                logs.append(f"{get_now()} {account_name} {100 * page_count}개 시작")
                params = {
                    "vendorId": self.account_common_info.get("partner_no"),  # 판매자 ID
                    "nextToken": next_token,  # 페이지 number
                    "maxPerPage": "100",  # 페이지당 건수
                    "createdAt": created_at,
                }

                query = parse.urlencode(params)
                url = self._urls.get("get_products_by_page")
                header = get_header(url=url, data=self.account_common_info, query=query)
                response = self.request.get(url=self.coupang_api + url, headers=header, params=params)
                if response.status_code == 200:
                    next_token = response.json()["nextToken"]
                    products = response.json()["data"]

                    for product in products:
                        # 변경 불가능한 상품 pass
                        if product["statusName"] == "상품삭제":
                            continue

                        if product["statusName"] == "심사중":
                            in_review_products.append([account_name, product.get("sellerProductId")])
                            continue

                        url = self._urls.get("get_product_info").format(product.get("sellerProductId"))
                        header = get_header(url=url, data=self.account_common_info)
                        response = self.request.get(self.coupang_api + url, headers=header, timeout=5)
                        form_data = response.json()["data"]

                        # 이미 반품지, 출고지 변경이 완료된 상품 pass
                        if form_data["returnCenterCode"] == self.return_info.get("returnCenterCode") \
                                and form_data["outboundShippingPlaceCode"] == self.outbound_info.get(
                            "outboundShippingPlaceCode") \
                                and form_data["statusName"] == "승인완료":
                            continue

                        form_data["returnCenterCode"] = self.return_info.get("returnCenterCode")
                        form_data["returnChargeName"] = self.return_info.get("returnChargeName")
                        form_data["companyContactNumber"] = self.return_info.get("companyContactNumber")
                        form_data["returnZipCode"] = self.return_info.get("returnZipCode")
                        form_data["returnAddress"] = self.return_info.get("returnAddress")
                        form_data["returnAddressDetail"] = self.return_info.get("returnAddressDetail")

                        form_data["outboundShippingPlaceCode"] = self.outbound_info.get("outboundShippingPlaceCode")

                        # 상품정보고시 및 옵션 속성
                        url = self._urls.get('product_type_info').format(form_data.get('displayCategoryCode'))
                        header = get_header(url=url, data=self.account_common_info)
                        response = self.request.get(self.coupang_api + url, headers=header, timeout=20)
                        if response.status_code != 200:
                            failure_products.append([str(product.get("sellerProductId")), response.text])
                            continue

                        # 상품정보고시
                        notice_categories = response.json().get('data').get('noticeCategories')
                        # 2021-01-22 기타재화 있으면 기타재화로 등록하고 없는 경우는 그 외 상품정보고시에 상세페이지 참조로 올린다.
                        # 만일 기타재화가 없는 상품들이 에러가 난다면 여기를 확인하고 수정해야한다.
                        other_product_notice_categories = [n for n in notice_categories if
                                                           n.get('noticeCategoryName') == '기타 재화']
                        product_types = []
                        if len(other_product_notice_categories) > 0:
                            for notice in other_product_notice_categories:
                                for notice_name in notice.get('noticeCategoryDetailNames'):
                                    product_types.append(
                                        dict(
                                            noticeCategoryName=notice.get('noticeCategoryName'),
                                            noticeCategoryDetailName=notice_name.get('noticeCategoryDetailName'),
                                            content='상세페이지 참조'
                                        )
                                    )
                        else:
                            for notice in notice_categories:
                                for notice_name in notice.get('noticeCategoryDetailNames'):
                                    product_types.append(
                                        dict(
                                            noticeCategoryName=notice.get('noticeCategoryName'),
                                            noticeCategoryDetailName=notice_name.get('noticeCategoryDetailName'),
                                            content='상세페이지 참조'
                                        )
                                    )

                        for item in form_data["items"]:
                            item["notices"] = product_types

                            # NOTE Value가 비어 있는 attribute 처리
                            attributes = item["attributes"]
                            delete_candidate_indices = list()
                            for a, attribute in enumerate(attributes):
                                if attribute.get("attributeValueName") == "" and attribute.get("exposed") == "EXPOSED":
                                    attribute["attributeValueName"] = "상세설명참조"
                                elif attribute.get("attributeValueName") == "" and attribute.get("exposed") == "NONE":
                                    delete_candidate_indices.append(a)
                            delete_candidate_indices.reverse()
                            for i in delete_candidate_indices:
                                attributes.pop(i)

                        if form_data["brand"] == "":
                            form_data["brand"] = "상세설명참조"

                        # NOTE 이미지 길이 수정
                        for item in form_data["items"]:
                            for image in item["images"]:
                                if len(image["vendorPath"]) > 150:
                                    image["vendorPath"] = parse.unquote(image["vendorPath"])

                        form_data["requested"] = True  # 자동으로 승인 요청

                        url = self._urls.get("edit_product")
                        header = get_header(url=url, method="PUT", data=self.account_common_info)
                        response = self.request.put(self.coupang_api + url, headers=header, timeout=5,
                                                    data=json.dumps(form_data))
                        rsp = response.json()
                        if rsp["code"] == "SUCCESS":
                            print(product.get("sellerProductId"), rsp["code"], "." * (len(logs) % 3 + 1), end="\r")
                            pass
                        else:
                            failure_products.append([str(product.get("sellerProductId")), rsp["message"]])
                            logs.append(f"{product.get('sellerProductId')}\t{rsp['code']}\t{rsp['message']}")

                    # 다음 페이지 없음
                    if not next_token:
                        break
                else:
                    # print("상품 조회 실패")
                    logs.append("상품 조회 실패")
                    raise ValueError("상품 조회 실패")

                # print(f"{get_now()} {account_name} {100 * page_count}개 완료")
                logs.append(f"{get_now()} {account_name} {100 * page_count}개 완료")
                save_logging(account_name, messages=logs)
                logs.clear()
                save_in_review_products(in_review_products)
                in_review_products.clear()
                page_count += 1
            except Exception as e:
                print(get_now(), e.__str__())
                logs.append(f"{get_now()} {e.__str__()}")
                save_failure_products(account_name, failure_infos=failure_products)
                save_logging(account_name, messages=logs)
                logs.clear()
                save_in_review_products(in_review_products)
                in_review_products.clear()
                time.sleep(60)
                continue
        # End of while

        save_failure_products(account_name, failure_infos=failure_products)
        save_logging(account_name, messages=logs)
        logs.clear()
        save_in_review_products(in_review_products)
        in_review_products.clear()


if __name__ == "__main__":
    while 1:
        utcnow = dt.datetime.utcnow()
        if utcnow.strftime("%H%M") == "0646":
            break
        else:
            time.sleep(33)
    accounts = accounts
    procs = list()
    for n, account in enumerate(accounts):
        proc = Process(target=CoupangEdit(data=account).renew_return_info)
        procs.append(proc)
        proc.start()
        print(f"{n + 1}번째 시작 ({account.get('name')})")

    for proc in procs:
        proc.join()

    print("전체 완료")


def save_failure_products(account_name: str, failure_infos: list):
    with open(f"./logs/edit_failed_products_{account_name}.txt", "a") as t:
        for failure_info in failure_infos:
            t.write(f"{failure_info[0]}\t{failure_info[1]}\n")


def save_logging(account_name: str, messages: list):
    with open(f"./logs/logs_{account_name}.txt", "a") as t:
        for message in messages:
            t.write(message + "\n")


def save_in_review_products(products: list):
    with open("./logs/in_review_products.txt", "a") as t:
        for product in products:
            t.write(f"{product[0]}\t{product[1]}\n")
