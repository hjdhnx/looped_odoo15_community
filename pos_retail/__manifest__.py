
{
    "name": "POS Retail",
    "category": "Point of Sale",
    "author": "E.Mudathir",
    "summary":
        """
       POS Loyality Program + Coupon + Promotion
        """,
    "description":
        """
          POS Loyality Program + Coupon + Promotion
        """,
    "sequence": 0,
    "depends": [
        "pos_restaurant",
        "sale_coupon",
        "pos_branch",
        "website_sale",
        "base_automation"
        
    ],
    "data": [
        "security/ir.model.access.csv",
        # "security/group.xml",
        # "security/ir_rule.xml",
        "views/Menu.xml",
        # "datas/pos_loyalty_category.xml",
        "datas/sequence.xml",
        "views/PosConfig.xml",
        # "views/PosLoyalty.xml",
        "views/PosWallet.xml",
        "views/ResPartner.xml",
        "views/PosPromotion.xml",
        "views/Restaurant.xml",
        "views/CouponProgram.xml",
        "views/pos_gift_coupon.xml",
        "views/report_pos_gift_coupon.xml",
        
    ],
    "application": True,
    
}
