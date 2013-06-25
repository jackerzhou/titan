#!/usr/local/bin/python2.7
#coding:utf-8

from flask import Blueprint
from utils.helper import make_view
from views.repos.repos import Create, View, Transport, Delete, \
        Setting, AddCommiter, RemoveCommiter

MODULE_NAME = 'repos'
view_func = make_view(MODULE_NAME)

repos = Blueprint(MODULE_NAME, __name__)

view = view_func(View)
create = view_func(Create)
setting = view_func(Setting)
commiters = view_func(AddCommiter, name='commiters', tmpl='commiters')
remove_commiter = view_func(RemoveCommiter, name='remove')
transport = view_func(Transport)
delete = view_func(Delete)

repos.add_url_rule('/<git>/new', view_func=create, methods=['GET', 'POST'])

repos.add_url_rule('/<git>/<rname>', view_func=view, methods=['GET'])
repos.add_url_rule('/<git>/<tname>/<rname>', view_func=view, methods=['GET'])

repos.add_url_rule('/<git>/<rname>/setting', view_func=setting, methods=['GET', 'POST'])
repos.add_url_rule('/<git>/<tname>/<rname>/setting', view_func=setting, methods=['GET', 'POST'])

repos.add_url_rule('/<git>/<rname>/commiters', view_func=commiters, methods=['GET', 'POST'])
repos.add_url_rule('/<git>/<tname>/<rname>/commiters', view_func=commiters, methods=['GET', 'POST'])

repos.add_url_rule('/<git>/<rname>/remove', view_func=remove_commiter, methods=['POST'])
repos.add_url_rule('/<git>/<tname>/<rname>/remove', view_func=remove_commiter, methods=['POST'])

repos.add_url_rule('/<git>/<rname>/transport', view_func=transport, methods=['POST'])
repos.add_url_rule('/<git>/<tname>/<rname>/transport', view_func=transport, methods=['POST'])

repos.add_url_rule('/<git>/<rname>/delete', view_func=setting, methods=['POST'])
repos.add_url_rule('/<git>/<tname>/<rname>/delete', view_func=setting, methods=['POST'])

