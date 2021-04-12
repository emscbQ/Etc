import requests


class LotteonCategory:
    def __init__(self):
        self.header = {
            "Authorization": "Bearer 5d5b2cb498f3d20001665f4eab9343a92969418194502784d68080fd",  # 스토어 센터에서 발급받은 인증키
            "Accept": "application/json",  # application / json과 application / xml을 지원함
            "Accept-Language": "ko",  # 국내 접속일 경우 ko
            "X-Timezone": "GMT+09:00",  # 시간 표현식의 기준 시간대. 국내는 GMT + 9시
            "Content-Type": "application/json",  # POST 호출 시에 필수값
        }
        self.urls = dict(
            search_std_ctg="https://onpick-api.lotteon.com/cheetah/econCheetah.ecn?job=cheetahStandardCategory&skip={skip}&limit={limit}",
        )

        # 긁은 정보
        self.category_infos = dict()  # { category_id: {depth: depth, name: category_name, parent_id: parent_category_id, is_leaf: is_leaf}, ... }

        # 엑셀에 넣을 결과물
        self.categories = [["대분류", "중분류", "소분류", "세분류", "카테고리_코드", "대중소세_합본", "사용가능여부"]]

    def category_command(self):
        self.get_category_infos()
        self.clean_up_category_infos()
        return self.categories
        # self.save_to_xlsx()

    def get_category_infos(self):
        coefficient = 1
        while True:
            response = requests.get(url=self.urls.get("search_std_ctg").format(skip=500 * (coefficient - 1), limit=500),
                                    headers=self.header)
            rsp = response.json()

            if not rsp["itemList"]:
                break

            for item in rsp["itemList"]:
                if item["data"]["use_yn"] == "Y":
                    data = item["data"]

                    depth = data["depth_no"]
                    category_name = data["std_cat_nm"]
                    category_id = data["std_cat_id"]
                    parent_category_id = data["upr_std_cat_id"]
                    is_leaf = data["leaf_yn"] == "Y"
                    self.category_infos[category_id] = dict(
                        depth=depth,
                        name=category_name,
                        parent_id=parent_category_id,
                        is_leaf=is_leaf,
                    )

            coefficient += 1

    def clean_up_category_infos(self):
        for category_id, infos in self.category_infos.items():
            XL, L, M, S = "", "", "", ""
            if infos["depth"] == "1":  # 대분류
                XL = infos["name"]
            elif infos["depth"] == "2":  # 중분류
                L = infos["name"]
                XL = self.category_infos[infos["parent_id"]].get("name")
            elif infos["depth"] == "3":  # 소분류
                M = infos["name"]
                L = self.category_infos[infos["parent_id"]].get("name")
                XL = self.category_infos[self.category_infos[infos["parent_id"]].get("parent_id")].get("name")
            elif infos["depth"] == "4":  # 세분류
                S = infos["name"]
                M = self.category_infos[infos["parent_id"]].get("name")
                L = self.category_infos[self.category_infos[infos["parent_id"]].get("parent_id")].get("name")
                XL = self.category_infos[
                    self.category_infos[self.category_infos[infos["parent_id"]].get("parent_id")].get("parent_id")].get(
                    "name")

            names = [XL, L, M, S]
            while True:
                try:
                    names.remove("")
                except ValueError:
                    break

            self.categories.append(
                [XL, L, M, S, category_id, ">".join(names), infos["is_leaf"]]
            )
            print("카테고리 추출 중" + "." * (len(self.categories) % 3 + 1), end="\r")
        print("카테고리 추출 완료!\n")
