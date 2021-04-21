import imgkit
import os

# os.system("rm out.jpg")
# imgkit.from_file("./test.html", "out.jpg")
# imgkit.from_url("http://google.com", "out.jpg")

import json

import requests

url = "http://localhost:8080/product-managing/collage"
header = {
    "Content-Type": "application/json",
    "accept": "application/json",
    "secret": "minions",
    # "origin": "decorating.justqkorea.com",
}

response = requests.post(url, data=json.dumps(dict(
    product_code="test_code",
    detail_image_html="""
            <TABLE cellSpacing=0 cellPadding=0 border=0><TBODY><TR><TD align=middle><div><img  src=http://image.dome4u.co.kr/data/editor/1611/1994202502_1478229564.95.jpg></div></TD></TR></TBODY></TABLE>
            """.strip(),
)), headers=header)

print(response)

response = requests.post(url+"/main", data=json.dumps(dict(
    product_code="test_code",
    main_image_url="""
            http://img2.domesin.com/data/shop/1/10000114_hKLyq.jpg
            """.strip(),
)), headers=header)

# response = requests.options(url, headers=header)

print(response)
