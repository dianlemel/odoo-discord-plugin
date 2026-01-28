{
    'name': 'Discord',
    'version': '19.0.0.0.7',
    'category': 'Technical',
    'author': "HE,XUE-DIAN",
    'depends': ['base', 'contacts', 'website', 'mail'],
    'description': "Discord 機器人",
    'data': [
        'security/ir.model.access.csv',
        'data/discord_command_data.xml',
        'data/message_template_data.xml',
        'views/menu.xml',
        'views/res_config.xml',
        'views/res_partner.xml',
        'views/discord_channel.xml',
        'views/discord_command.xml',
        'views/message_template.xml',
        'views/payment_templates.xml',
        'views/points_order.xml',
        'views/points_gift.xml',
    ],
    "external_dependencies": {
        "python": ['discord', 'jinja2'],
    },
    'assets': {
        'web.assets_backend': [
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'post_init_hook': '_post_init_hook',
}
