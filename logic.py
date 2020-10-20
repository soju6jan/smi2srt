# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
import threading

# third-party

# sjva 공용
from framework import db, scheduler, app, celery
from framework.job import Job
from framework.util import Util


# 패키지
from .plugin import logger, package_name
from .model import ModelSetting, ModelSmi2srtFile
from .smi2srt_handle import SMI2SRTHandle
#########################################################

class Logic(object):
    db_default = { 
        'db_version' : '1',
        'auto_start' : 'False',
        'interval' : '13',
        'work_path' : '',
        'flag_remake' : 'False',
        'flag_remove_smi' : 'True',
        'flag_append_ko' : 'True',
        'flag_change_ko_srt' : 'True',
        'fail_file_move' : 'False',
        'fail_move_path' : '',
        'not_smi_move_path' : '',
    }

    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
            #Logic.migration()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_load():
        try:
            Logic.db_init()
            if ModelSetting.query.filter_by(key='auto_start').first().value == 'True':
                Logic.scheduler_start()
            from .plugin import plugin_info
            Util.save_from_dict_to_json(plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_unload():
        pass

    @staticmethod
    def scheduler_start():
        try:
            job = Job(package_name, package_name, ModelSetting.get('interval'), Logic.scheduler_function, u"SMI to SRT", False)
            scheduler.add_job_instance(job)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def scheduler_stop():
        try:
            scheduler.remove_job(package_name)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def scheduler_function():
        try:
            if app.config['config']['use_celery']:
                result = Logic.start_by_path.apply_async()
                result.get()
            else:
                Logic.start_by_path()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def reset_db():
        try:
            db.session.query(ModelSmi2srtFile).delete()
            db.session.commit()
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False


    @staticmethod
    def one_execute():
        try:
            if scheduler.is_include(package_name):
                if scheduler.is_running(package_name):
                    ret = 'is_running'
                else:
                    scheduler.execute_job(package_name)
                    ret = 'scheduler'
            else:
                def func():
                    time.sleep(2)
                    Logic.scheduler_function()
                threading.Thread(target=func, args=()).start()
                ret = 'thread'
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            ret = 'fail'
        return ret

    """
    @staticmethod
    def migration():
        try:
            db_version = ModelSetting.get('db_version')
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    """
    #########################################################


    
    @staticmethod
    @celery.task
    def start_by_path(work_path=None):
        try:
            if work_path is None:
                work_paths = [x.strip() for x in ModelSetting.get('work_path').split(',')]
            else:
                work_paths = [x.strip() for x in work_path.split(',')]
            logger.debug('start_by_path : %s', work_paths)
            fail_move_path = ModelSetting.get('fail_move_path') if ModelSetting.get_bool('fail_file_move') and ModelSetting.get('fail_move_path') != '' else ''
            not_smi_move_path = ModelSetting.get('not_smi_move_path') if ModelSetting.get_bool('fail_file_move') and ModelSetting.get('not_smi_move_path') != '' else ''
            for work_path in work_paths:
                result = SMI2SRTHandle.start(work_path, remake=ModelSetting.get_bool('flag_remake'), no_remove_smi=not ModelSetting.get_bool('flag_remove_smi'), no_append_ko=not ModelSetting.get_bool('flag_append_ko'), no_change_ko_srt=not ModelSetting.get_bool('flag_change_ko_srt'), fail_move_path=fail_move_path, not_smi_move_path=not_smi_move_path)
                #logger.debug(result)
                ModelSmi2srtFile.save(result)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
