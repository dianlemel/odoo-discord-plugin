{
    'name': 'Discord',
    'version': '19.0.0.0.5',
    'category': 'Technical',
    'author': "HE,XUE-DIAN",
    'depends': ['base', 'contacts', 'website', 'mail'],
    'description': "Discord 機器人",
    'data': [
        'security/ir.model.access.csv',
        'data/discord_command_data.xml',
        'views/res_config.xml',
        'views/res_partner.xml',
        'views/discord_channel.xml',
        'views/discord_command.xml',
        'views/transform_templates.xml',
        'views/payment_templates.xml',
        'views/points_order.xml',
    ],
    "external_dependencies": {
        "python": ['discord'],
    },
    'assets': {
        'web.assets_backend': [
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
