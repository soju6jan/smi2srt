# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
from datetime import datetime
import json

# third-party
from sqlalchemy import or_, and_, func, not_, desc
from sqlalchemy.orm import backref

# sjva 공용
from framework import db, path_app_root, app
from framework.util import Util

# 패키지
from .plugin import logger, package_name
#########################################################

app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (os.path.join(path_app_root, 'data', 'db', '%s.db' % package_name))

class ModelSetting(db.Model):
    __tablename__ = '%s_setting' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)
 
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

    @staticmethod
    def get(key):
        try:
            return db.session.query(ModelSetting).filter_by(key=key).first().value.strip()
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())
            
    
    @staticmethod
    def get_int(key):
        try:
            return int(ModelSetting.get(key))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def get_bool(key):
        try:
            return (ModelSetting.get(key) == 'True')
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def set(key, value):
        try:
            item = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
            if item is not None:
                item.value = value.strip()
                db.session.commit()
            else:
                db.session.add(ModelSetting(key, value.strip()))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def to_dict():
        try:
            ret = Util.db_list_to_dict(db.session.query(ModelSetting).all())
            ret['package_name'] = package_name
            return ret 
        except Exception as e:
            logger.error('Exception:%s ', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                if key in ['scheduler', 'is_running']:
                    continue
                entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
            db.session.commit()
            return True                  
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            logger.debug('Error Key:%s Value:%s', key, value)
            return False
       

class ModelSmi2srtFile(db.Model):
    __tablename__ = '%s_item' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    change_type = db.Column(db.String)
    created_time = db.Column(db.DateTime)
    smi_file = db.Column(db.String)
    result = db.Column(db.String)
    json = db.Column(db.JSON)

    def __init__(self, result):
        if 'log' in result:
            result['log'] = result['log'].replace('<', '&lt;').replace('>', '&gt;')
        self.change_type = 'smi'
        self.created_time = datetime.now()
        self.smi_file = result['smi_file']
        self.result = result['ret']
        self.json = result


    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S') 
        ret['json'] = ret['json'] if isinstance(ret['json'], dict) else  json.loads(ret['json'])
        return ret
    
    
    @staticmethod
    def save(data):
        try:
            for d in data['list']:
                #logger.debug(d)
                item = db.session.query(ModelSmi2srtFile).filter_by(smi_file=d['smi_file']).all()
                for t in item:
                    db.session.delete(t)
                db.session.add(ModelSmi2srtFile(d))
            db.session.commit()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc()) 



    @staticmethod
    def web_list(req):
        try:
            ret = {}
            page = 1
            page_size = 30
            job_id = ''
            search = ''
            if 'page' in req.form:
                page = int(req.form['page'])
            if 'search_word' in req.form:
                search = req.form['search_word']
            result_type = req.form['result_type']
            query = db.session.query(ModelSmi2srtFile)
            if search != '':
                query = query.filter(ModelSmi2srtFile.smi_file.like('%'+search+'%'))
            if result_type == 'success':
                query = query.filter(ModelSmi2srtFile.result == 'success')
            elif result_type == 'fail':
                query = query.filter(ModelSmi2srtFile.result == 'fail')
            elif result_type == 'etc':
                query = query.filter(ModelSmi2srtFile.result != 'success').filter(ModelSmi2srtFile.result != 'fail')
            
            count = query.count()
            query = (query.order_by(desc(ModelSmi2srtFile.id))
                        .limit(page_size)
                        .offset((page-1)*page_size)
                )
            logger.debug('ModelSmi2srtFile count:%s', count)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = Util.get_paging_info(count, page, page_size)
            return ret
        except Exception as e:
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())

