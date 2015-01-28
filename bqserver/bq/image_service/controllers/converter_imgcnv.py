# converter_imgcnv.py
# Author: Dmitry Fedorov
# Center for BioImage Informatics, University California, Santa Barbara
from __future__ import with_statement

""" BioImageConvert command line converter
"""

__module__    = "converter_imgcnv"
__author__    = "Dmitry Fedorov"
__version__   = "1.3"
__revision__  = "$Rev$"
__date__      = "$Date$"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import logging
import os.path
from itertools import groupby
from lxml import etree
#from subprocess import call
from bq.util.locks import Locks

from tg import config
#from collections import OrderedDict
from bq.util.compat import OrderedDict
import bq.util.io_misc as misc

from .converter_base import ConverterBase, Format

log = logging.getLogger('bq.image_service.converter_imgcnv')

try:
    import dicom
except (ImportError, OSError):
    log.warn('pydicom needs to be installed for DICOM support...')
    pass


# Map DICOM Specific Character Set to python equivalent
dicom_encoding = {
    '': 'iso8859',           # default character set for DICOM
    'ISO_IR 6': 'iso8859',   # alias for latin_1 too
    'ISO_IR 100': 'latin_1',
    'ISO 2022 IR 87': 'iso2022_jp',
    'ISO 2022 IR 13': 'iso2022_jp',  #XXX this mapping does not work on chrH32.dcm test files (but no others do either)
    'ISO 2022 IR 149': 'euc_kr',   # XXX chrI2.dcm -- does not quite work -- some chrs wrong. Need iso_ir_149 python encoding
    'ISO_IR 192': 'UTF8',     # from Chinese example, 2008 PS3.5 Annex J p1-4
    'GB18030': 'GB18030',
    'ISO_IR 126': 'iso_ir_126',  # Greek
    'ISO_IR 127': 'iso_ir_127',  # Arab
    'ISO_IR 138': 'iso_ir_138', # Hebrew
    'ISO_IR 144': 'iso_ir_144', # Russian
}

def dicom_init_encoding(dataset):
    encoding = dataset.get(('0008', '0005'), 'ISO_IR 6')
    if not encoding in dicom_encoding:
        return 'latin_1'
    return dicom_encoding[encoding]

def safedecode(s, encoding):
    if isinstance(s, unicode) is True:
        return s
    if isinstance(s, basestring) is not True:
        return u'%s'%s
    try: 
        return s.decode(encoding)
    except UnicodeEncodeError:
        try: 
            return s.decode('utf8')
        except UnicodeEncodeError:
            return unicode(s.encode('ascii', 'replace'))

def dicom_parse_date(v):
    # first take care of improperly stored values
    if len(v)<1:
        return v
    if '.' in v:
        return v.replace('.', '-')
    if '/' in v:
        return v.replace('/', '-')
    # format proper value
    return '%s-%s-%s'%(v[0:4], v[4:6], v[6:8])

def dicom_parse_time(v):
    # first take care of improperly stored values
    if len(v)<1:
        return v
    if ':' in v:
        return v
    if '.' in v:
        return v.replace('.', ':')
    # format proper value
    return '%s:%s:%s'%(v[0:2], v[2:4], v[4:6])



################################################################################
# ConverterBase
################################################################################

class ConverterImgcnv(ConverterBase):
    installed = False
    version = None
    installed_formats = None
    CONVERTERCOMMAND = 'imgcnv' if os.name != 'nt' else 'imgcnv.exe'
    info_map = {
        'width'      : 'image_num_x',
        'height'     : 'image_num_y',
        'zsize'      : 'image_num_z',
        'tsize'      : 'image_num_t',
        'channels'   : 'image_num_c',
        'pages'      : 'image_num_p',
        'format'     : 'format',
        'pixelType'  : 'image_pixel_format',
        'depth'      : 'image_pixel_depth',
        'endian'     : 'endian',
        'dimensions' : 'dimensions'
    }

#     #######################################
#     # Init
#     #######################################
#
#     @classmethod
#     def init(cls):
#         #ConverterBase.init.im_func(cls)
#         ConverterBase.init(cls)
#         cls.get_formats()

    #######################################
    # Version and Installed
    #######################################

    @classmethod
    def get_version (cls):
        '''returns the version of command line utility'''
        o = misc.run_command( [cls.CONVERTERCOMMAND, '-v'] )
        try:
            d = [int(s) for s in o.split('.', 1)]
        except ValueError:
            log.error ('imgcnv is too old, cannot proceed')
            raise Exception('imgcnv is too old, cannot proceed')
        d.append(0)
        return {
            'full': '.'.join([str(i) for i in d]),
            'numeric': d,
            'major': d[0],
            'minor': d[1],
            'build': d[2]
        }

    #######################################
    # Formats
    #######################################

    @classmethod
    def get_formats(cls):
        '''inits supported file formats'''
        if cls.installed_formats is None:
            formats_xml = misc.run_command( [cls.CONVERTERCOMMAND, '-fmtxml'] )
            formats = etree.fromstring( '<formats>%s</formats>'%formats_xml )

            cls.installed_formats = OrderedDict()
            codecs = formats.xpath('//codec')
            for c in codecs:
                try:
                    name = c.get('name')
                    fullname = c.xpath('tag[@name="fullname"]')[0].get('value', '')
                    exts = c.xpath('tag[@name="extensions"]')[0].get('value', '').split('|')
                    reading = len(c.xpath('tag[@name="support" and @value="reading"]'))>0
                    writing = len(c.xpath('tag[@name="support" and @value="writing"]'))>0
                    multipage = len(c.xpath('tag[@name="support" and @value="writing multiple pages"]'))>0
                    metadata = len(c.xpath('tag[@name="support" and @value="reading metadata"]'))>0 or len(c.xpath('tag[@name="support" and @value="writing metadata"]'))>0
                    samples_min = misc.safeint(c.xpath('tag[@name="min-samples-per-pixel"]')[0].get('value', '0'))
                    samples_max = misc.safeint(c.xpath('tag[@name="max-samples-per-pixel"]')[0].get('value', '0'))
                    bits_min = misc.safeint(c.xpath('tag[@name="min-bits-per-sample"]')[0].get('value', '0'))
                    bits_max = misc.safeint(c.xpath('tag[@name="max-bits-per-sample"]')[0].get('value', '0'))
                except IndexError:
                    continue
                cls.installed_formats[name.lower()] = Format(
                    name=name,
                    fullname=fullname,
                    ext=exts,
                    reading=reading,
                    writing=writing,
                    multipage=multipage,
                    metadata=metadata,
                    samples=(samples_min,samples_max),
                    bits=(bits_min,bits_max)
                )

    #######################################
    # Supported
    #######################################

    @classmethod
    def supported(cls, ifnm, **kw):
        '''return True if the input file format is supported'''
        log.debug('Supported for: %s', ifnm )
        supported = cls.run_read(ifnm, [cls.CONVERTERCOMMAND, '-supported', '-i', ifnm]) 
        return supported.startswith('yes')


    #######################################
    # Meta - returns a dict with all the metadata fields
    #######################################

    @classmethod
    def meta(cls, ifnm, series=0, **kw):
        '''returns a dict with file metadata'''
        log.debug('Meta for: %s', ifnm)
        if not cls.installed:
            return {}

        meta = cls.run_read(ifnm, [cls.CONVERTERCOMMAND, '-meta', '-i', ifnm] )
        if meta is None:
            return {}
        rd = {}
        for line in meta.splitlines():
            if not line: continue
            try:
                tag, val = [ l.lstrip() for l in line.split(':', 1) ]
            except ValueError:
                continue
            rd[tag] = misc.safetypeparse(val.replace('\n', ''))

        if 'dimensions' in rd:
            rd['dimensions'] = rd['dimensions'].replace(' ', '') # remove spaces

        if rd['image_num_z']==1 and rd['image_num_t']==1 and rd['image_num_p']>1:
            rd['image_num_t'] = rd['image_num_p']
        rd['image_num_series'] = 0
        rd['image_series_index'] = 0
        
        if cls.is_multifile_series(**kw) is True:
            rd.update(kw['token'].meta)
            #try:
            #    del rd['files']
            #except (KeyError):
            #    pass

        return rd

    #######################################
    # The info command returns the "core" metadata (width, height, number of planes, etc.)
    # as a dictionary
    #######################################
    
    @classmethod
    def info(cls, ifnm, series=0, **kw):
        '''returns a dict with file info'''
        log.debug('Info for: %s', ifnm)
        if not cls.installed:
            return {}
        if not os.path.exists(ifnm):
            return {}

        info = cls.run_read(ifnm, [cls.CONVERTERCOMMAND, '-info', '-i', ifnm] )
        if info is None:
            return {}
        rd = {}
        for line in info.splitlines():
            if not line: continue
            try:
                tag, val = [ l.strip() for l in line.split(':',1) ]
            except ValueError:
                continue
            if tag not in cls.info_map:
                continue
            rd[cls.info_map[tag]] = misc.safetypeparse(val.replace('\n', ''))

        # change the image_pixel_format output, convert numbers to a fully descriptive string
        if isinstance(rd['image_pixel_format'], (long, int)):
            pf_map = {
                1: 'unsigned integer', 
                2: 'signed integer', 
                3: 'floating point'
            }
            rd['image_pixel_format'] = pf_map[rd['image_pixel_format']]

        if 'dimensions' in rd:
            rd['dimensions'] = rd['dimensions'].replace(' ', '') # remove spaces

        rd['image_num_series'] = 0
        rd['image_series_index'] = 0
        rd.setdefault('image_num_z', 1)
        rd.setdefault('image_num_t', 1)
        rd.setdefault('image_num_p', 1)
        if rd['image_num_z']==1 and rd['image_num_t']==1 and rd['image_num_p']>1:
            rd['image_num_t'] = rd['image_num_p']
        
        if cls.is_multifile_series(**kw) is True:
            rd.update(kw['token'].meta)
            #try:
            #    del rd['files']
            #except (KeyError):
            #    pass
        
        return rd

    #######################################
    # multi-file series misc
    #######################################

    @classmethod
    def write_files(cls, files, ofnm):
        '''writes a list of files into a file readable by imgcnv'''
        with open(ofnm, 'wb') as f:
            f.write('\n'.join(files))

    #######################################
    # Conversion
    #######################################

    @classmethod
    def convert(cls, ifnm, ofnm, fmt=None, series=0, extra=None, **kw):
        '''converts a file and returns output filename'''
        log.debug('convert: [%s] -> [%s] into %s for series %s with [%s]', ifnm, ofnm, fmt, series, extra)
        command = []
        
        if cls.is_multifile_series(**kw) is False:
            command.extend(['-i', ifnm])
        else:
            # use first image of the series, need to check for separate channels here
            files = cls.enumerate_series_files(**kw)
            log.debug('convert files: %s', files)
            # create a list file and pass that as input
            fl = '%s.files'%ofnm
            cls.write_files(files, fl)
            command.extend(['-il', fl])
            
            # provide geometry and resolution
            meta = kw['token'].meta or {}

            geom = '%s,%s'%(meta.get('image_num_z', 1),meta.get('image_num_t', 1))
            command.extend(['-geometry', geom])
            
            res = '%s,%s,%s,%s'%(meta.get('pixel_resolution_x', 0), meta.get('pixel_resolution_y', 0), meta.get('pixel_resolution_z', 0), meta.get('pixel_resolution_t', 0))
            command.extend(['-resolution', res])
        
        if ofnm is not None:
            command.extend (['-o', ofnm])
        if fmt is not None:
            command.extend (['-t', fmt])
            if cls.installed_formats[fmt].multipage is True:
                extra.extend(['-multi'])
            else:
                extra.extend(['-page', '1'])
        if extra is not None:
            command.extend (extra)
        return cls.run(ifnm, ofnm, command )

    #def convertToOmeTiff(cls, ifnm, ofnm, series=0, extra=[]):
    #    '''converts input filename into output in OME-TIFF format'''
    #    return cls.convert(ifnm, ofnm, ['-input', ifnm, '-output', ofnm, '-format', 'OmeTiff', '-series', '%s'%series] )

    @classmethod
    def thumbnail(cls, ifnm, ofnm, width, height, series=0, **kw):
        '''converts input filename into output thumbnail'''
        log.debug('Thumbnail: %s %s %s for [%s]', width, height, series, ifnm)
        fmt = kw.get('fmt', 'jpeg')
        preproc = kw.get('preproc', '')
        preproc = preproc if preproc != '' else 'mid' # use 'mid' as auto mode for imgcnv
        
        command = ['-o', ofnm, '-t', fmt]
        
        try:
            token = kw.get('token', None)
            info = token.dims or {}
        except (TypeError, AttributeError):
            info = {}
        
        log.debug('info: %s', info)
        
        num_z = info.get('image_num_z', 1)
        num_t = info.get('image_num_t', 1)
        page=1
        if preproc == 'mid':
            mx = num_z if num_z>1 else num_t
            page = min(max(1, mx/2), mx)
        elif preproc != '':
            return None
        
        # separate normal and multi-file series
        if cls.is_multifile_series(**kw) is False:
            command.extend(['-i', ifnm])
            command.extend(['-page', str(page)])
        else:
            # use first image of the series, need to check for separate channels here
            files = cls.enumerate_series_files(**kw)
            log.debug('thumbnail files: %s', files)
            command.extend(['-i', files[page-1]])

        if info.get('image_pixel_depth', 16) != 8:
            command.extend(['-depth', '8,d'])

        #command.extend(['-display'])
        command.extend(['-fusemeta'])
        if info.get('image_num_c', 1)<4:
            command.extend(['-fusemethod', 'm'])
        else:
            command.extend(['-fusemethod', 'm']) # 'a'
            
        method = kw.get('method', 'BC')
        command.extend([ '-resize', '%s,%s,%s,AR'%(width,height,method)])
        if fmt == 'jpeg':
            command.extend([ '-options', 'quality 95 progressive yes'])

        return cls.run(ifnm, ofnm, command )

    @classmethod
    def slice(cls, ifnm, ofnm, z, t, roi=None, series=0, **kw):
        '''extract Z,T plane from input filename into output in OME-TIFF format'''
        log.debug('Slice: z=%s t=%s roi=%s series=%s for [%s]', z, t, roi, series, ifnm)
        z1,z2 = z
        t1,t2 = t
        x1,x2,y1,y2 = roi
        fmt = kw.get('fmt', 'bigtiff')
        token = kw.get('token', None)
        info = token.dims if token is not None else None

        command = ['-o', ofnm, '-t', fmt]

        if t2==0: 
            t2=t1
        if z2==0: 
            z2=z1

        pages = []
        for ti in range(t1, t2+1):
            for zi in range(z1, z2+1):
                if info['image_num_t']==1:
                    page_num = zi
                elif info['image_num_z']==1:
                    page_num = ti
                elif info.get('dimensions', 'XYCZT').replace(' ', '').startswith('XYCT') is False:
                    page_num = (ti-1)*info['image_num_z'] + zi
                else:
                    page_num = (zi-1)*info['image_num_t'] + ti
                pages.append(page_num)
        
        log.debug('slice pages: %s', pages)
        
        # separate normal and multi-file series
        if cls.is_multifile_series(**kw) is False:
            command.extend(['-i', ifnm])
            command.extend(['-multi', '-page', ','.join([str(p) for p in pages])])
        else:
            # use first image of the series, need to check for separate channels here
            command.extend(['-multi'])
            files = cls.enumerate_series_files(**kw)
            if len(pages)==1 and (x1==x2 or y1==y2):
                # in multi-file case and only one page is requested with no ROI, return with no re-conversion 
                misc.dolink(files[pages[0]-1], ofnm)
                return ofnm
            else:
                for p in pages:
                    command.extend(['-i', files[p-1]])
        
        # roi
        if not x1==x2 or not y1==y2:
            if not x1==x2:
                if x1>0: x1 = x1-1
                if x2>0: x2 = x2-1
            if not y1==y2:
                if y1>0: y1 = y1-1
                if y2>0: y2 = y2-1
            command.extend(['-roi', '%s,%s,%s,%s' % (x1,y1,x2,y2)])

        return cls.run(ifnm, ofnm, command )

    #######################################
    # Special methods
    #######################################

    def writeHistogram(self, channels, ofnm):
        '''writes Histogram in libbioimage format'''
        log.debug('Writing histogram into: %s', ofnm )
        
        import struct
        with open(ofnm, 'wb') as f:
            f.write(struct.pack('<cccc', 'B', 'I', 'M', '1')) # header
            f.write(struct.pack('<cccc', 'I', 'H', 'S', '1')) # spec
            f.write(struct.pack('<L', channels)) # number of histograms
            # write histograms
            for c in range(channels):
                f.write(struct.pack('<cccc', 'B', 'I', 'M', '1')) # header
                f.write(struct.pack('<cccc', 'H', 'S', 'T', '1')) # spec
                
                # write bim::HistogramInternal 
                f.write(struct.pack('<H', 8)) # uint16 data_bpp; // bits per pixel
                f.write(struct.pack('<H', 1)) # uint16 data_fmt; // signed, unsigned, float
                f.write(struct.pack('<d', 0.0)) # double shift;
                f.write(struct.pack('<d', 1.0)) # double scale;
                f.write(struct.pack('<d', 0.0)) # double value_min;
                f.write(struct.pack('<d', 255.0)) # double value_max;
                
                # write data
                f.write(struct.pack('<L', 256)) # histogram size, here 256
                for i in range(256):
                    f.write(struct.pack('<Q', 100)) # histogram data, here each color has freq of 100


    #######################################
    # Sort and organize files
    #
    # DICOM files in a directory need to be sorted and combined into series
    # we need to use the following tags in the following order to group files into series
    # then, each group should be sorted based on instance number tag
    #
    #(0010, 0020) Patient ID                          LO: 'ANON85099405877'
    #(0020, 000d) Study Instance UID                  UI: 2.16.840.1.113786.1.52.850.674495585.766
    #(0020, 000e) Series Instance UID                 UI: 2.16.840.1.113786.1.52.850.674495585.767
    #(0020, 0011) Series Number                       IS: '2'
    #
    #(0020, 0013) Instance Number                     IS: '1'
    #
    #######################################

    @classmethod
    def group_files_dicom(cls, files, **kw):
        '''return list with lists containing grouped and ordered dicom file paths'''

        import dicom # ensure an error if dicom library is not installed

        def read_tag(ds, key, default=None):
            t = ds.get(key)
            if t is None:
                return ''
            return t.value or default

        if not cls.installed:
            return False
        log.debug('Group %s files', len(files) )
        data = []
        groups = []
        blobs = []
        for f in files:
            try:
                ds = dicom.read_file(f)
            except (Exception):
                blobs.append(f)
                continue

            if 'PixelData' not in ds:
                blobs.append(f)
                continue                

            modality     = read_tag(ds, ('0008', '0060'))
            patient_id   = read_tag(ds, ('0010', '0020'))
            study_uid    = read_tag(ds, ('0020', '000d'))
            series_uid   = read_tag(ds, ('0020', '000e'))
            series_num   = read_tag(ds, ('0020', '0012')) # 
            acqui_num    = read_tag(ds, ('0020', '0011')) # A number identifying the single continuous gathering of data over a period of time that resulted in this image
            instance_num = int(read_tag(ds, ('0020', '0013'), '0') or '0') # A number that identifies this image
            dr_suffix    = int(read_tag(ds, ('4453', '1005'), '0') or '0') # some DR Systems produced data seems to have a bug in writing wrong instance numbers and site locations
            num_temp_p   = int(read_tag(ds, ('0020', '0105'), '0') or '0') # Total number of temporal positions prescribed
            num_frames   = int(read_tag(ds, ('0028', '0008'), '0') or '0') # Number of frames in a Multi-frame Image

            key = '%s/%s/%s/%s/%s'%(modality, patient_id, study_uid, series_uid, acqui_num) # series_num seems to vary in DR Systems
            data.append((key, dr_suffix or instance_num, f, num_temp_p or num_frames))
            #log.debug('Key: %s, series_num: %s, instance_num: %s, num_temp_p: %s, num_frames: %s', key, series_num, instance_num, num_temp_p, num_frames )
        
        # group based on a key
        data = sorted(data, key=lambda x: x[0])
        for k, g in groupby(data, lambda x: x[0]):
            # sort based on an instance_num
            groups.append( sorted(list(g), key=lambda x: x[1]) )
        
        # prepare groups of dicom filenames
        images   = []
        geometry = []
        for g in groups:
            l = [f[2] for f in g]
            images.append( l )
            if len(l) == 1:
                geometry.append({ 't': 1, 'z': 1 })
            elif f[3]>0:
                z = len(l) / f[3]
                geometry.append({ 't': f[3], 'z': z })
            else:
                geometry.append({ 't': 1, 'z': len(l) })

        log.debug('group_files_dicom found: %s image groups, %s blobs', len(images), len(blobs))

        return (images, blobs, geometry)
    
    #######################################
    # DICOM metadata parser writing directly into XML tree
    #######################################
    
    @classmethod
    def meta_dicom(cls, ifnm, series=0, xml=None, **kw):
        '''appends nodes to XML'''
        
        import dicom # ensure an error if dicom library is not installed

        def recurse_tree(dataset, parent, encoding='latin-1'):
            for de in dataset:
                if de.tag == ('7fe0', '0010'):
                    continue
                node = etree.SubElement(parent, 'tag', name=de.name, type=':///DICOM#%04.x,%04.x'%(de.tag.group, de.tag.element))

                if de.VR == "SQ":   # a sequence
                    for i, dataset in enumerate(de.value):
                        recurse_tree(dataset, node, encoding)
                else:
                    if isinstance(de.value, dicom.multival.MultiValue):
                        value = ','.join(safedecode(i, encoding) for i in de.value)
                    else:                
                        value = safedecode(de.value, encoding)
                    try:
                        node.set('value', value)
                    except (ValueError):
                        pass

        try:
            _, tmp = misc.start_nounicode_win(ifnm, [])
            ds = dicom.read_file(tmp or ifnm)
        except (Exception):
            misc.end_nounicode_win(tmp)
            return
        encoding = dicom_init_encoding(ds)
        recurse_tree(ds, xml, encoding=encoding)     
        
        misc.end_nounicode_win(tmp)
        return

    #######################################
    # Most important DICOM metadata to be ingested directly into data service
    #######################################
    
    @classmethod
    def meta_dicom_parsed(cls, ifnm, xml=None, **kw):
        '''appends nodes to XML'''
        
        import dicom # ensure an error if dicom library is not installed

        def append_tag(dataset, tag, parent, name=None, fmt=None, safe=True, encoding='latin-1'):
            de = dataset.get(tag, None)
            if de is None:
                return
            name = name or de.name
            typ = ':///DICOM#%04.x,%04.x'%(de.tag.group, de.tag.element)
            
            if fmt is None:
                if isinstance(de.value, dicom.multival.MultiValue):
                    value = ','.join(safedecode(i, encoding) for i in de.value)
                else:                
                    value = safedecode(de.value, encoding)
            else:
                if safe is True:
                    try:
                        value = fmt(safedecode(de.value, encoding))
                    except (Exception):
                        value = safedecode(de.value, encoding)
                else:
                    value = fmt(safedecode(de.value, encoding))
            if len(value)>0:
                node = etree.SubElement(parent, 'tag', name=name, value=value, type=typ)

        try:
            _, tmp = misc.start_nounicode_win(ifnm, [])
            ds = dicom.read_file(tmp or ifnm)
        except (Exception):
            misc.end_nounicode_win(tmp)
            return 

        encoding = dicom_init_encoding(ds)

        append_tag(ds, ('0010', '0020'), xml, encoding=encoding) # Patient ID
        try:
            append_tag(ds, ('0010', '0010'), xml, name='Patient\'s Last Name', safe=False, fmt=lambda x: x.split('^', 1)[0], encoding=encoding ) # Patient's Name
            append_tag(ds, ('0010', '0010'), xml, name='Patient\'s First Name', safe=False, fmt=lambda x: x.split('^', 1)[1], encoding=encoding ) # Patient's Name
        except (Exception):
            append_tag(ds, ('0010', '0010'), xml, encoding=encoding ) # Patient's Name
        append_tag(ds, ('0010', '0040'), xml, encoding=encoding) # Patient's Sex 'M'
        append_tag(ds, ('0010', '1010'), xml, encoding=encoding) # Patient's Age '019Y'
        append_tag(ds, ('0010', '0030'), xml, fmt=dicom_parse_date ) # Patient's Birth Date
        append_tag(ds, ('0012', '0062'), xml, encoding=encoding) # Patient Identity Removed
        append_tag(ds, ('0008', '0020'), xml, fmt=dicom_parse_date ) # Study Date
        append_tag(ds, ('0008', '0030'), xml, fmt=dicom_parse_time ) # Study Time
        append_tag(ds, ('0008', '0060'), xml, encoding=encoding) # Modality
        append_tag(ds, ('0008', '1030'), xml, encoding=encoding) # Study Description
        append_tag(ds, ('0008', '103e'), xml, encoding=encoding) # Series Description
        append_tag(ds, ('0008', '0080'), xml, encoding=encoding) # Institution Name  
        append_tag(ds, ('0008', '0090'), xml, encoding=encoding) # Referring Physician's Name
        append_tag(ds, ('0008', '0008'), xml) # Image Type
        append_tag(ds, ('0008', '0012'), xml, fmt=dicom_parse_date ) # Instance Creation Date
        append_tag(ds, ('0008', '0013'), xml, fmt=dicom_parse_time ) # Instance Creation Time
        append_tag(ds, ('0008', '1060'), xml, encoding=encoding) # Name of Physician(s) Reading Study
        append_tag(ds, ('0008', '2111'), xml, encoding=encoding) # Derivation Description  
        
        misc.end_nounicode_win(tmp)

try:
    ConverterImgcnv.init()
except Exception:
    log.warn("Imgcnv not available")
