{
    'name': 'Discord',
    'version': '19.0.0.0.1',
    'category': 'Technical',
    'author': "HE,XUE-DIAN",
    'depends': ['base', 'sale_management'],
    'description': "Discord 機器人",
    'data': [
        'security/ir.model.access.csv',
        'views/ecpay_templates.xml',
        'views/res_config.xml',
    ],
    "external_dependencies": {
        "python": [],
    },
    'assets': {
        'web.assets_backend': [
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
