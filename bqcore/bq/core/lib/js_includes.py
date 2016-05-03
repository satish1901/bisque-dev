# -*- coding: utf-8 -*-

"""WebHelpers used in bqcore."""

import tg
from minimatic import *

import bq
from bq.util.paths import bisque_path

def generate_css_files(root=None, public=None):
    production = False if root is None else True
    root = root or bisque_path('')
    public = public or bisque_path('public')

    if production or tg.config.get('bisque.js_environment', None) == 'production':
        css_kw = dict (fs_root=public,
                    combined='/css/all_css.css',
                    combined_path = root + '/bqcore/bq/core/public/css/all_css.css',
                    checkts = False,
                    version=bq.release.__VERSION_HASH__ )
    else:
        css_kw = {}

    return stylesheet_link (
        '/css/bq.css',
        '/css/bq_ui_toolbar.css',
        '/js/bq_ui_misc.css',
        '/js/ResourceBrowser/ResourceBrowser.css',
        '/js/ResourceTagger/Tagger.css',
        '/js/DatasetBrowser/DatasetBrowser.css',
        '/js/Share/BQ.share.Dialog.css',
        '/js/settings/BQ.settings.Panel.css',
        '/js/admin/BQ.user.Manager.css',
        '/js/picker/Path.css',
        '/js/tree/files.css',
        '/js/tree/organizer.css',
        { 'file' : '/image_service/public/converter.css', 'path' : root + 'bqserver/bq' },
        '/panojs3/styles/panojs.css',
        '/js/slider/slider.css',
        '/js/picker/Color.css',
        '/js/form/field/Color.css',
        '/css/imgview.css',
        '/js/movie/movie.css',
        { 'file': '/dataset_service/public/dataset_panel.css', 'path' : root + 'bqserver/bq' },
        '/js/renderers/dataset.css',
        '/js/graphviewer/graphviewer.css',
        '/js/volume/bioWeb3D.css',
        {'file' : '/import_service/public/bq_ui_upload.css', 'path' : root + 'bqserver/bq'},
        {'file' : '/export_service/public/css/BQ.Export.css', 'path' : root + 'bqserver/bq'},
        '/css/bisquik_extjs_fix.css',

        # -- modules
        '/js/modules/bq_ui_renderes.css',
        '/js/modules/bq_webapp.css',


        # -- plugin css
        plugins = { 'path': root + 'bqcore/bq/core/public/plugins/', 'file': '/plugins/' },

        # combined will not work for now due to relative urls in .css files
        #fs_root=public,
        #combined='/css/all_css.css',
        #combined_path = root + '/bqcore/bq/core/public/css/all_css.css',
        #checkts = False,
        #version=bq.release.__VERSION_HASH__

        **css_kw
    )

def generate_js_files(root=None, public=None):
    production = False if root is None else True
    root = root or bisque_path('')
    public = public or bisque_path('public')

    if production or tg.config.get('bisque.js_environment', None) == 'production':
        link_kw = dict (fs_root = public,
                      combined= '/js/all_js.js',
                      combined_path = root + '/bqcore/bq/core/public/js/all_js.js',
                      checkts = False,
                      minify= 'minify', # D3 breaks with minify
                      version=bq.release.__VERSION_HASH__)
    else:
        link_kw = {}

    return javascript_link(

        # Pre-required libraries
        #'/d3/d3.js',
        #'/threejs/three.js',
        '/threejs/TypedArrayUtils.js',
        '/threejs/math/ColorConverter.js',
        #-- Async.js --
        #'/async/async.js',
        #-- jquery --
        #'/jquery/jquery.min.js',
        #-- proj4 --
        #'/proj4js/proj4.js',
        #-- Raphael --
        #'/raphael/raphael.js',
        #-- kinetic --
        #'/js/viewer/kinetic-v5.1.0.js',

        #'/js/bq_ui_extjs_fix.js',
        # --Bisque JsApi - this needs cleaning and updating--
        '/js/utils.js',
        '/js/bq_api.js',
        '/js/bq_ui_application.js',
        '/js/bq_ui_toolbar.js',
        '/js/bq_ui_misc.js',
        '/js/date.js',
        '/js/encoder.js',

        # -- ResourceBrowser code --
        '/js/ResourceBrowser/Browser.js',
        '/js/ResourceBrowser/LayoutFactory.js',
        '/js/ResourceBrowser/ResourceQueue.js',
        '/js/ResourceBrowser/DatasetManager.js',
        '/js/ResourceBrowser/CommandBar.js',
        '/js/ResourceBrowser/viewStateManager.js',
        '/js/ResourceBrowser/OperationBar.js',
        '/js/ResourceBrowser/ResourceFactory/ResourceFactory.js',
        '/js/ResourceBrowser/ResourceFactory/ResourceImage.js',
        '/js/ResourceBrowser/ResourceFactory/ResourceMex.js',
        '/js/ResourceBrowser/ResourceFactory/ResourceModule.js',
        '/js/ResourceBrowser/ResourceFactory/ResourceDataset.js',
        '/js/ResourceBrowser/ResourceFactory/ResourceFile.js',
        '/js/ResourceBrowser/ResourceFactory/ResourceUser.js',
        '/js/ResourceBrowser/ResourceFactory/ResourceTemplate.js',
        '/js/ResourceBrowser/ResourceFactory/ResourceDir.js',
        '/js/ResourceBrowser/Misc/MessageBus.js',
        '/js/ResourceBrowser/Misc/Slider.js',
        '/js/ResourceBrowser/Misc/DataTip.js',

        # -- Gesture manager --
        '/js/senchatouch/sencha-touch-gestures.js',
        '/js/ResourceBrowser/Misc/GestureManager.js',

        # -- Share dialog files --
        '/js/Share/BQ.share.Dialog.js',
        '/js/Share/BQ.share.Multi.js',

        # -- ResourceTagger --
        '/js/ResourceTagger/ComboBox.js',
        '/js/ResourceTagger/RowEditing.js',
        '/js/ResourceTagger/Tagger.js',
        '/js/ResourceTagger/TaggerOffline.js',
        '/js/ResourceTagger/ResourceRenderers/BaseRenderer.js',

        # -- Preferences --
        '/js/Preferences/BQ.Preferences.js',
        '/js/Preferences/PreferenceViewer.js',
        '/js/Preferences/PreferenceTagger.js',

        # -- Settings Page --
        '/js/settings/BQ.settings.Panel.js',
        '/js/settings/BQ.ModuleManager.js',
        '/js/settings/BQ.ModuleDeveloper.js',
        '/js/settings/BQ.PreferenceManager.js',

        # -- Admin --
        '/js/admin/BQ.user.Manager.js',

        # -- Modules --
        '/js/modules/bq_webapp.js',
        '/js/modules/bq_module_webapp_default.js',
        '/js/modules/bq_webapp_service.js',

        #-- DatasetBrowser --
        {'file': '/dataset_service/public/dataset_service.js', 'path': root + 'bqserver/bq/'},
        '/js/DatasetBrowser/DatasetBrowser.js',

        # -- TemplateManager --
        '/js/TemplateManager/TemplateTagger.js',
        '/js/TemplateManager/TemplateManager.js',
        '/js/TemplateManager/TagRenderer.js',

        # -- Tree Organizer --
        '/js/picker/Path.js',
        '/js/tree/files.js',
        '/js/tree/organizer.js',

        # -- PanoJS3 --
        '/panojs3/panojs/utils.js',
        '/panojs3/panojs/PanoJS.js',
        '/panojs3/panojs/controls.js',
        '/panojs3/panojs/pyramid_Bisque.js',
        '/panojs3/panojs/control_thumbnail.js',
        '/panojs3/panojs/control_info.js',
        '/panojs3/panojs/control_svg.js',

        # -- Image Service --
        { 'file' : '/image_service/public/converter.js', 'path': root + 'bqserver/bq/'},
        { 'file' : '/image_service/public/bq_is_formats.js', 'path': root + 'bqserver/bq/'},

        '/js/slider/inversible.js',
        '/js/slider/slider.js',
        '/js/slider/tslider.js',
        '/js/slider/zslider.js',

        '/js/picker/AnnotationStatus.js',
        '/js/picker/Color.js',
        '/js/form/field/Color.js',

        '/js/viewer/menu_gobjects.js',
        '/js/viewer/scalebar.js',
        '/js/viewer/2D.js',
        '/js/viewer/imgview.js',
        '/js/viewer/imgops.js',
        '/js/viewer/imgslicer.js',
        '/js/viewer/imgstats.js',
        '/js/viewer/listner_zoom.js',
        '/js/viewer/tilerender.js',
        '/js/viewer/svgrender.js',
        '/js/viewer/shapeanalyzer.js',
        '/js/viewer/canvasshapes.js',
        '/js/viewer/canvasrender.js',
        '/js/viewer/imgedit.js',
        '/js/viewer/imgmovie.js',
        '/js/viewer/imageconverter.js',
        '/js/viewer/imgexternal.js',
        '/js/viewer/imgscalebar.js',
        '/js/viewer/imginfobar.js',
        '/js/viewer/progressbar.js',
        '/js/viewer/widget_extjs.js',
        '/js/viewer/imgpixelcounter.js',
        '/js/viewer/imgcurrentview.js',
        '/js/viewer/imgcalibration.js',


        #-- Movie player --
        '/js/movie/movie.js',

        #-- Stats --
        { 'file' : '/stats/public/js/stats.js', 'path': root + 'bqserver/bq/'},
        '/js/bq_ui_progress.js',

        #-- GMaps API --
        '/js/map/map.js',

        #-- Resource dispatch --
        { 'file': '/dataset_service/public/dataset_service.js','path': root + 'bqserver/bq/'},
        { 'file': '/dataset_service/public/dataset_operations.js','path': root + 'bqserver/bq/'},
        { 'file': '/dataset_service/public/dataset_panel.js','path': root + 'bqserver/bq/'},
        '/js/renderers/dataset.js',
        '/js/resourceview.js',

        # -- Import Service --
        { 'file' : '/import_service/public/File.js', 'path': root + 'bqserver/bq/'},
        { 'file' : '/import_service/public/bq_file_upload.js', 'path': root + 'bqserver/bq/'},
        { 'file' : '/import_service/public/bq_ui_upload.js', 'path': root + 'bqserver/bq/'},

        # -- Export Service --
        { 'file' : '/export_service/public/js/BQ.Export.js', 'path': root + 'bqserver/bq/'},

        # -- Request Animation Frame --
        '/js/requestAnimationFrame.js',

        # -- Graph viewer --
        '/js/d3Component.js',
        '/js/graphviewer/dagre-d3.js',
        '/js/graphviewer/GraphViewer.js',

        # -- WebGL viewer --
        '/js/volume/lib/whammy.js',
        '/js/volume/lib/polygon.js',
        '/js/volume/threejs/AnaglyphEffect.js',
        '/js/volume/threejs/RotationControls.js',
        '/js/volume/threejs/OrbitControls.js',
        '/js/volume/threejs/TrackballControls.js',
        '/js/volume/volumeConfig.js',
        '/js/volume/renderingControls.js',
        '/js/volume/lightingControls.js',
        '/js/volume/animationControls.js',
        '/js/volume/extThreeJS.js',
        '/js/volume/gobjectbuffers.js',
        '/js/picker/Excolor.js',
        '/js/volume/transferEditorD3.js',
        '/js/volume/scalebar.js',
        '/js/volume/bioWeb3D.js',
        '/js/volume/lightingControls.js',

        # -- Modules --
        '/js/modules/bq_grid_panel.js',
        '/js/modules/bq_ui_renderes.js',

        # -- plugin renderers
        plugins = { 'path': root + 'bqcore/bq/core/public/plugins/', 'file': '/plugins/' },

        # --
        **link_kw
    )

