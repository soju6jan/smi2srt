# -*- coding: UTF-8 -*-
'''
@package smi2srt
@brief this module is for convert .smi subtitle file into .srt subtitle 
    (Request by Alfred Chae)

Started : 2011/08/08
license: GPL

@version: 1.0.0
@author: Moonchang Chae <mcchae@gmail.com>
'''
# Moonchang Chae님 파일 수정본
# hojel님의 demux 부분 가져옴 (https://github.com/hojel/SmiConvert.bundle)
# SJVA, Plex plugin, 쉘 공용
import os
import sys
import re
import codecs
import shutil
import sys
import traceback
import logging
import io

logger = None
try:
    # SJVA
    from framework import py_unicode, app
    from framework.util import Util
    from .plugin import logger, package_name
except:
    pass

def log_debug(msg, *args, **kwargs):
    if logger is not None:
        logger.debug(msg, *args, **kwargs)
    else:
        Log(msg, *args, **kwargs)

def log_info(msg, *args, **kwargs):
    if logger is not None:
        logger.info(msg, *args, **kwargs)
    else:
        Log(msg, *args, **kwargs)

class smiItem(object):
    def __init__(self):
        self.start_ms = 0
        self.end_ms = 0
        self.start_ts = '00:00:00,000'
        self.end_ts = '00:00:00,000'
        self.contents = None
        self.linecount = 0
    @staticmethod
    def ms2ts(ms):
        hours = int(ms / 3600000)
        ms = ms - hours * 3600000
        minutes = int(ms / 60000)
        ms = ms - minutes * 60000
        seconds = int(ms / 1000)
        ms = ms - seconds * 1000
        s = '%02d:%02d:%02d,%03d' % (hours, minutes, seconds, ms)
        return s
    def convertSrt(self):
        if self.linecount == 4:
            i=1 #@UnusedVariable
        # 1) convert timestamp
        self.start_ts = smiItem.ms2ts(self.start_ms)
        self.end_ts = smiItem.ms2ts(self.end_ms-10)
        # 2) remove new-line
        self.contents = re.sub(r'\s+', ' ', self.contents)
        # 3) remove web string like "&nbsp";
        self.contents = re.sub(r'&[a-z]{2,5};', '', self.contents)
        # 4) replace "<br>" with '\n';
        self.contents = re.sub(r'(<br>)+', '\n', self.contents, flags=re.IGNORECASE)
        # 5) find all tags
        fndx = self.contents.find('<')
        if fndx >= 0:
            contents = self.contents
            sb = self.contents[0:fndx]
            contents = contents[fndx:]
            while True:
                m = re.match(r'</?([a-z]+)[^>]*>([^<>]*)', contents, flags=re.IGNORECASE)
                if m == None: break
                contents = contents[m.end(2):]
                #if m.group(1).lower() in ['font', 'b', 'i', 'u']:
                if m.group(1).lower() in ['b', 'i', 'u']:
                    sb += m.string[0:m.start(2)]
                sb += m.group(2)
            self.contents = sb
        self.contents = self.contents.strip()
        self.contents = self.contents.strip('\n')
    def __repr__(self):
        s = '%d:%d:<%s>:%d' % (self.start_ms, self.end_ms, self.contents, self.linecount)
        return s


class SMI2SRTHandle(object):
    remake = False
    no_remove_smi = False
    no_append_ko = False
    no_change_ko_srt = False
    fail_move_path = False
    result_list = None
    not_smi_move_path = None
    
    @staticmethod
    def start(work_path, remake=False, no_remove_smi=False, no_append_ko=False, no_change_ko_srt=False, fail_move_path='', not_smi_move_path=''):
        SMI2SRTHandle.remake = remake
        SMI2SRTHandle.no_remove_smi = no_remove_smi
        SMI2SRTHandle.no_append_ko = no_append_ko
        SMI2SRTHandle.no_change_ko_srt = no_change_ko_srt
        SMI2SRTHandle.fail_move_path = fail_move_path
        SMI2SRTHandle.not_smi_move_path = not_smi_move_path
        SMI2SRTHandle.result_list = {}
        SMI2SRTHandle.result_list['option'] = {'work_path':work_path, 'remake':remake, 'no_remove_smi':no_remove_smi, 'no_append_ko':no_append_ko, 'no_change_ko_srt':no_change_ko_srt, 'fail_move_path':fail_move_path, 'not_smi_move_path':not_smi_move_path}
        SMI2SRTHandle.result_list['list'] = []
        try:
            work_path = work_path
            if os.path.isdir(work_path):
                SMI2SRTHandle.convert_directory(work_path)
            else:
                parent_path = os.path.dirname(work_path)
                lists = [os.path.basename(work_path)]
                SMI2SRTHandle.convert_directory(parent_path, lists)
            return SMI2SRTHandle.result_list
        except Exception as e: 
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())

    @staticmethod
    def convert_directory(work_path, lists=None):
        logger.debug("convert_directory : <%s>" % work_path)
        try:
            if lists is None:
                lists = os.listdir(py_unicode(work_path))
            for item in lists:
                try:
                    eachfile = os.path.join(work_path, item)
                    if os.path.isdir(eachfile):
                        SMI2SRTHandle.convert_directory(eachfile)
                    elif os.path.isfile(eachfile):
                        if eachfile[-4:].lower() == '.smi':
                            rndx = eachfile.rfind('.')
                            if SMI2SRTHandle.no_append_ko or eachfile.lower().endswith('.kor.smi') or eachfile.lower().endswith('.ko.smi'):
                                srt_file = '%s.srt' % eachfile[0:rndx]
                            else:
                                srt_file = '%s.ko.srt' % eachfile[0:rndx]
                            if os.path.exists(srt_file):
                                if SMI2SRTHandle.remake:
                                    #logger.debug('remake is true..')
                                    pass
                                else:
                                    #logger.debug('remake is false..')
                                    # 2021-12-19
                                    if not SMI2SRTHandle.no_remove_smi:
                                        logger.debug("remove smi")
                                        os.remove(eachfile)
                                    continue
                            logger.debug('=========================================')
                            logger.debug("Convert start : <%s>" % eachfile)
                            logger.debug('srt filename : %s', srt_file)
                            ret = SMI2SRTHandle.convert_one_file_logic(eachfile, srt_file)
                            log_info("Convert result : %s", ret)
                            if ret['ret'] == "success":
                                if not SMI2SRTHandle.no_remove_smi:
                                    logger.debug("remove smi")
                                    os.remove(eachfile)
                            elif ret['ret'] == "not_smi":
                                if SMI2SRTHandle.not_smi_move_path:
                                    target = os.path.join(SMI2SRTHandle.not_smi_move_path, item)
                                    if eachfile != target:
                                        shutil.move(eachfile, target)
                                        ret['move_path'] = target
                            elif ret['ret'] == "fail":
                                if SMI2SRTHandle.fail_move_path:
                                    target = os.path.join(SMI2SRTHandle.fail_move_path, item)
                                    if eachfile != target:
                                        shutil.move(eachfile, target)
                                        ret['move_path'] = target
                            elif ret['ret'] == "continue":
                                continue
                            elif ret['ret'] == "not_smi_is_ass":
                                shutil.move(eachfile, srt_file.replace('.srt', '.ass'))
                                ret['move_path'] = srt_file.replace('.srt', '.ass')
                                logger.debug("move to ass..")
                            elif ret['ret'] == "not_smi_is_srt":
                                shutil.move(eachfile, srt_file)
                                ret['move_path'] = srt_file
                                logger.debug("move to srt..")
                            #elif ret['ret'] == "not_smi_is_torrent":
                            #    shutil.move(eachfile, eachfile.replace('.smi', '.torrent'))
                            #    logger.debug("move to torrent..")
                            SMI2SRTHandle.result_list['list'].append(ret)
                        elif eachfile[-7:].lower() == '.ko.srt' or eachfile[-8:].lower() == '.kor.srt' or (eachfile[-7]== '.' and  eachfile[-4:].lower()== '.srt'):
                            #logger.debug("pass : %s", eachfile)
                            pass
                        elif eachfile[-4:].lower() == '.srt':
                            if not SMI2SRTHandle.no_change_ko_srt:
                                logger.debug(".srt => .ko.srt : %s", eachfile)
                                # 2020-06-15 한글이 들어있는 파일만.
                                # 할 필요있나?..
                                shutil.move(eachfile, eachfile.replace('.srt', '.ko.srt'))
                except Exception as e: 
                    logger.debug('Exception:%s', e)
                    logger.debug(traceback.format_exc())

        except Exception as e: 
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())

    @staticmethod
    def predict_encoding(file_path, n_lines=100):
        '''Predict a file's encoding using chardet'''
        try:
            #raise Exception
            import chardet

            # Open the file as binary data
            with io.open(file_path, 'rb') as f:
                # Join binary lines for specified number of lines
                rawdata = b''.join([f.readline() for _ in range(n_lines)])
            logger.debug(chardet.detect(rawdata)['encoding'].lower())
            return chardet.detect(rawdata)['encoding'].lower()
        except Exception as e: 
            logger.debug('Exception:%s', e)
        
        try:
            ifp = io.open(file_path, 'rb')
            aBuf = ifp.read()
            ifp.close()
            
            # If the data starts with BOM, we know it is UTF
            if aBuf[:3] == '\xEF\xBB\xBF':
                # EF BB BF  UTF-8 with BOM
                result = "UTF-8"
            elif aBuf[:2] == '\xFF\xFE':
                # FF FE  UTF-16, little endian BOM
                result = "UTF-16LE"
            elif aBuf[:2] == '\xFE\xFF':
                # FE FF  UTF-16, big endian BOM
                result = "UTF-16BE"
            elif aBuf[:4] == '\xFF\xFE\x00\x00':
                # FF FE 00 00  UTF-32, little-endian BOM
                result = "UTF-32LE"
            elif aBuf[:4] == '\x00\x00\xFE\xFF': 
                # 00 00 FE FF  UTF-32, big-endian BOM
                result = "UTF-32BE"
            elif aBuf[:4] == '\xFE\xFF\x00\x00':
                # FE FF 00 00  UCS-4, unusual octet order BOM (3412)
                result = "X-ISO-10646-UCS-4-3412"
            elif aBuf[:4] == '\x00\x00\xFF\xFE':
                # 00 00 FF FE  UCS-4, unusual octet order BOM (2143)
                result = "X-ISO-10646-UCS-4-2143"
            else:
                result = "ascii"
            logger.debug('code chardet result:%s', result)
            return result
        except Exception as e: 
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())

    @staticmethod
    def convert_one_file_logic(smi_file, srt_file):
        try:
            ret = {'smi_file':smi_file}
            if not os.path.exists(smi_file):
                return {'ret':'fail'}

            encoding = SMI2SRTHandle.predict_encoding(smi_file).lower()
            
            if encoding is not None:
                if encoding.startswith('utf-16') or encoding.startswith('utf-8'):
                    encoding2 = encoding
                else:
                    encoding2 = 'cp949'
                logger.debug('File encoding : %s %s', encoding, encoding2)
                #if encoding == 'EUC-KR' or encoding == 'ascii' or encoding == 'Windows-1252' or encoding == 'ISO-8859-1':
                #   encoding = 'cp949'
                ret['encoding1'] = encoding
                ret['encoding2'] = encoding2
                try:
                    ifp = codecs.open(smi_file, 'r', encoding=encoding2)
                    smi_sgml = ifp.read() 
                    smi_sgml = smi_sgml.encode('utf-8')
                    ret['is_success_file_read'] = True
                except Exception as e:
                    ret['is_success_file_read'] = False
                    #logger.debug('Exception:%s', e)
                    #logger.debug(traceback.format_exc())
                    logger.debug('line read logic start..')
                    ifp = io.open(smi_file, 'rb')
                    lines = []
                    count = 0
                    while True:
                        try:
                            line = ifp.readline()
                            if not line: 
                                break
                            #lines.append(unicode(line, encoding.lower()).encode('utf-8'))
                            lines.append(line.decode(encoding.lower()).encode('utf-8'))
                        except Exception as ee:
                            logger.error(ee)
                            count += 1
                            pass
                    logger.debug('line except count :%s', count)
                    smi_sgml = b'\n'.join(lines)
                    ret['except_line_count'] = count
            else:
                return {'ret':'fail'}


            data = SMI2SRTHandle.demuxSMI(smi_sgml)
            ret['lang_count'] = len(data)
            ret['srt_list'] = []
            #for lang, smi_sgml in data.iteritems():
            for lang, smi_sgml in data.items():
                logger.debug('lang info : %s', lang)
                try:
                    try:
                        fndx = smi_sgml.upper().find('<SYNC')
                    except Exception as e:
                        raise e

                    if fndx < 0:
                        ret['ret'] = SMI2SRTHandle.process_not_sync_tag(smi_sgml)
                        return ret
                    smi_sgml = smi_sgml[fndx:]
                    lines = smi_sgml.split('\n')
                    
                    srt_list = []
                    sync_cont = ''
                    si = None
                    last_si = None
                    linecnt = 0
                    #logger.debug(len(lines))
                    for index, line in enumerate(lines):
                        linecnt += 1
                        sndx = line.upper().find('<SYNC')
                        if sndx >= 0:
                            m = re.search(r'<sync\s+start\s*=\s*(\d+)>(.*)$', line, flags=re.IGNORECASE)
                            if not m:
                                m = re.search(r'<sync\s+start\s*=\s*(\d+)\send\s*=(\d+)>(.*)$', line, flags=re.IGNORECASE)
                            if not m:
                                m = re.search(r'<sync\s+start\s*=-\s*(\d+)>(.*)$', line, flags=re.IGNORECASE)
                            if not m:
                                # <SYNC Start="100">, 마지막 > 태그 없는거
                                m = re.search(r'<SYNC\s+Start\s*=\"?(\d+)\"?>?(.*)$', line, flags=re.IGNORECASE)
                            if not m:
                                #<SYNC S tart=1562678
                                m = re.search(r'<sync\s+s\s*t\s*a\s*r\s*t\s*=\s*(\d+)>(.*)$', line, flags=re.IGNORECASE)
                            if not m:
                                line2 = line.lower().replace('<sync start=>', '<sync start=0>')
                                #2019-09-15
                                line2 = line2.lower().replace('<sync start=nan>', '<sync start=0>')
                                line2 = line2.lower().replace("<sync st,rt=", '<sync start=')
                                line2 = line2.lower().replace("<sync s,art=", '<sync start=')
                                m = re.search(r'<sync\s+start\s*=\s*(\d+)>(.*)$', line2, flags=re.IGNORECASE)
                            # 2021-12-19 start=1111 에러가 너무 많음
                            if not m:
                                m = re.search(r'<sync\s+\w+=?\s*(\d+)>(.*)$', line2, flags=re.IGNORECASE)

                            if not m:
                                #2020-06-15 음수.
                                m = re.search(r'<sync\s+start\s*=-(\d+)', line, flags=re.IGNORECASE)
                                if m:
                                    ret['log'] = u'-시간 태그 있음.'
                                    continue
                            if not m:
                                if index == len(lines)-1:
                                    #맨 마지막 문장이라면 pass
                                    ret['log'] = u'마지막 문장 %s 으로 끝남.' % line.strip()
                                    continue
                                elif line.strip().upper() == '<SYNC':
                                    # 종종 보임. 어짜피 다음 태그가 정상이니 패스
                                    continue
                                else:
                                    ret['log'] = u'태그 분석 실패. %s:%s' % (index, line)
                                    raise Exception('AAAAAA format tag of <Sync start=nnnn> with "%s:%s"' % (index, line.strip()))
                            sync_cont += line[0:sndx]
                            last_si = si
                            if last_si != None:
                                last_si.end_ms = int(m.group(1))
                                last_si.contents = sync_cont
                                srt_list.append(last_si)
                                last_si.linecount = linecnt
                            sync_cont = m.group(2)
                            si = smiItem()
                            si.start_ms = int(m.group(1))
                        else:
                            sync_cont += line
                            
                    #ofp = io.open(srt_file, 'w', encoding="utf8")
                    #ofp = open(srt_file, 'w')
                    if lang == 'KRCC':
                        tmp_srt_file = srt_file
                    else:
                        if srt_file.endswith('.ko.srt'):
                            tmp_srt_file = srt_file.replace('.ko.srt', '.%s.srt' % lang.lower()[:2])
                        else:
                            tmp_srt_file = srt_file.replace('.srt', '.%s.srt' % lang.lower()[:2])

                    ofp = codecs.open(tmp_srt_file, 'w', encoding='utf8')
                    ndx = 1
                    for si in srt_list:
                        si.convertSrt()
                        if si.contents == None or len(si.contents) <= 0:
                            continue
                        sistr = '%d\n%s --> %s\n%s\n\n' % (ndx, si.start_ts, si.end_ts, si.contents)
                        #sistr = py_unicode(sistr, 'utf-8').encode('euc-kr')
                        sistr = py_unicode(sistr)
                        ofp.write(sistr)
                        ndx += 1
                    ofp.close()
                    ret['srt_list'].append({'lang':lang, 'srt_file':tmp_srt_file })
                except Exception as e: 
                    logger.debug('Exception:%s', e)
                    logger.debug(traceback.format_exc())
                    ret['ret'] = 'fail'
                    return ret
            ret['ret'] = 'success'
            return ret
        except Exception as e: 
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())
            ret['ret'] = 'fail'
            return ret

    @staticmethod
    def process_not_sync_tag(text):
        try:
            logger.debug('NO SYNC TAG')
            if text.strip().startswith('[Script Info]'):
                return "not_smi_is_ass"
            result = re.compile(r'\d{2}\:\d{2}\:\d{2}\,\d{3}').findall(text)
            if len(result) > 10:
                return "not_smi_is_srt"
            #if text.strip().startswith('d8:announce'):
            #    return "not_smi_is_torrent"
            return "not_smi"
        except Exception as e: 
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())

    @staticmethod
    def demuxSMI(smi_sgml):
        try:
            if app.config['config']['is_py3']:
                smi_sgml = smi_sgml.decode()
            #LANG_PTN = re.compile("^\s*\.([A-Z]{2}CC) *{ *[Nn]ame:.*; *[Ll]ang: *(\w{2})-(\w{2});.*}", re.M|re.I)
            LANG_PTN = re.compile("^\s*\.([A-Z]{2}CC)", re.M|re.I)
            CLASS_PTN = re.compile("<[Pp] [Cc]lass=([A-Z]{2}CC)>")
            CLOSETAG_PTN = re.compile("</(BODY|SAMI)>", re.I)

            langinfo = LANG_PTN.findall(smi_sgml)

            if len(langinfo) < 2:
                return {'KRCC':smi_sgml}
            result = dict()
            lines = smi_sgml.split('\n')
            #for capClass, lang, country in langinfo:
            for capClass in langinfo:
                outlines = []
                passLine = True
                for line in lines:
                    query = CLASS_PTN.search(line)
                    if query:
                        curCapClass = query.group(1)
                        passLine = True if curCapClass == capClass else False
                    if passLine or CLOSETAG_PTN.search(line):
                        outlines.append(line)
                if len(outlines) > 100:
                    result[capClass] = '\n'.join(outlines)
                
            
            return result
        except Exception as e: 
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    import argparse
    parser = argparse.ArgumentParser(description = u'SMI to SRT')
    parser.add_argument('work_path', type=str, help=u"디렉토리나 파일")
    
    parser.add_argument('--remake', required=False, help=u"srt 파일이 있는 경우에도 재생성. (생략시 패스)", action="store_true", default=False)
    parser.add_argument('--no_remove_smi', required=False, help=u"변환 후 smi 파일을 삭제하지 않음. (생략시 삭제)", action="store_true", default=False)
    parser.add_argument('--no_append_ko', required=False, help=u"파일명에 ko 등을 추가하지 않음. (생략시 추가)", action="store_true", default=False)
    parser.add_argument('--no_change_ko_srt', required=False, help=u".srt 파일을 .ko.srt로 변경하지 않음. (생략시 변경함)", action="store_true", default=False)
    parser.add_argument('--fail_move_path', required=False, help=u"실패시 이동할 폴더. (생략시 이동하지 않음)", default="")

    args = parser.parse_args()
    logger.debug("args:%s", args)
    #SMI2SRTHandle.start(args)
    
    ret = SMI2SRTHandle.start(args.work_path, remake=args.remake, no_remove_smi=args.no_remove_smi, no_append_ko=args.no_append_ko, no_change_ko_srt=args.no_change_ko_srt, fail_move_path=args.fail_move_path)
