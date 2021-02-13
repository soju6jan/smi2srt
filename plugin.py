# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import threading
import time

# third-party
import requests
from flask import Blueprint, request, Response, render_template, redirect, jsonify, redirect
from flask_login import login_user, logout_user, current_user, login_required

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler
from framework.util import Util

# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
from .logic import Logic
from .model import ModelSetting, ModelSmi2srtFile
#########################################################


blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

menu = {
    'main' : [package_name, u'SMI to SRT'],
    'sub' : [
        ['setting', u'설정'], ['list', u'처리결과'], ['log', u'로그']
    ],
    'category' : 'fileprocess'
}  

plugin_info = {
    'version' : '0.1.0.0',
    'name' : u'smi2srt',
    'category_name' : 'fileprocess',
    'developer' : 'soju6jan',
    'description' : u'smi to srt 변환',
    'home' : 'https://github.com/soju6jan/smi2srt',
    'more' : '',
}

def plugin_load():
    Logic.plugin_load()

def plugin_unload():
    Logic.plugin_unload()


#########################################################
# WEB Menu   
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/list' % package_name)

@blueprint.route('/<sub>')
@login_required
def first_menu(sub): 
    if sub == 'setting':
        arg = ModelSetting.to_dict()
        arg['scheduler'] = str(scheduler.is_include(package_name))
        arg['is_running'] = str(scheduler.is_running(package_name))
        return render_template('%s_setting.html' % package_name, arg=arg)
    elif sub == 'list':
        arg = ModelSetting.to_dict()
        return render_template('%s_list.html' % package_name, arg=arg)
    elif sub == 'log':
        return render_template('log.html', package=package_name)
    return render_template('sample.html', title='%s - %s' % (package_name, sub))

#########################################################
# For UI                                                          
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def ajax(sub):
    logger.debug('AJAX %s %s', package_name, sub)
    try:
        if sub == 'setting_save':
            ret = ModelSetting.setting_save(request)
            return jsonify(ret)
        elif sub == 'scheduler':
            go = request.form['scheduler']
            if go == 'true':
                Logic.scheduler_start()
            else:
                Logic.scheduler_stop()
            return jsonify(go)
        elif sub == 'one_execute':
            ret = Logic.one_execute()
            return jsonify(ret)
        elif sub == 'reset_db':
            ret = Logic.reset_db()
            return jsonify(ret)
        elif sub == 'web_list':
            ret = ModelSmi2srtFile.web_list(request)
            return jsonify(ret)
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())  
