ssg_api = "https://eapi.ssgadm.com"
urls = dict(
    get_items=ssg_api + "/item/{version}/getItemList.ssg".format(version="0.1"),
    get_item_detail=ssg_api + "/item/{version}/viewItem.ssg".format(version="0.3"),
    get_props=ssg_api + "/common/{version}/listItemMngPropCls.ssg".format(version="0.2"),
    get_prop_detail=ssg_api + "/common/{version}/listItemMngProp.ssg".format(version="0.1"),
    get_category=ssg_api + "/venInfo/{version}/listStdCtgKeyPath.ssg".format(version="0.2"),
    get_common_code=ssg_api + "/common/{version}/getCommCdDtlc.ssg".format(version="0.1"),
    post_shipping_delay=ssg_api + "/api/pd/{version}/listShppingDelay.ssg".format(version="1"),
    post_list_warehouse_out=ssg_api + "/api/pd/{version}/listWarehouseOut.ssg".format(version="1"),
    post_no_sell_request=ssg_api + "/api/pd/{version}/saveNoSellRequestRegist.ssg".format(version="1"),
)
account_info = dict(
    access_key="c5294a5f-6a6f-49e6-b806-1d9ae98753a6"
)

header = {
    "Authorization": account_info.get("access_key"),  # 업체 인증키
    "Accept": "application/json",
    "Content-Type": "application/json"
}
