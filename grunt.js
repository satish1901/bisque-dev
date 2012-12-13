/* Bisque grunt configuration to package and minify project JS files */
/* add new js files to the below list for processing */
module.exports = function(grunt) {

  grunt.initConfig({
    concat: {
      dist: {
        src: [
        'public/js/bq_ui_extjs_fix.js',
        'public/js/utils.js',
        'public/js/bq_api.js',
        'public/js/bq_ui_application.js',
        'public/js/bq_ui_toolbar.js',
        'public/js/bq_ui_misc.js',
        'public/js/date.js',
        'public/js/encoder.js',
        'public/js/ResourceBrowser/Browser.js',
        'public/js/ResourceBrowser/LayoutFactory.js',
        'public/js/ResourceBrowser/Organizer.js',
        'public/js/ResourceBrowser/ResourceQueue.js',
        'public/js/ResourceBrowser/DatasetManager.js',
        'public/js/ResourceBrowser/CommandBar.js',
        'public/js/ResourceBrowser/viewStateManager.js',
        'public/js/ResourceBrowser/OperationBar.js',
        'public/js/ResourceBrowser/ResourceFactory/ResourceFactory.js',
        'public/js/ResourceBrowser/ResourceFactory/ResourceImage.js',
        'public/js/ResourceBrowser/ResourceFactory/ResourceMex.js',
        'public/js/ResourceBrowser/ResourceFactory/ResourceModule.js',
        'public/js/ResourceBrowser/ResourceFactory/ResourceDataset.js',
        'public/js/ResourceBrowser/ResourceFactory/ResourceFile.js',
        'public/js/ResourceBrowser/ResourceFactory/ResourceUser.js',
        'public/js/ResourceBrowser/ResourceFactory/ResourceTemplate.js',
        'public/js/ResourceBrowser/Misc/MessageBus.js',
        'public/js/ResourceBrowser/Misc/Slider.js',
        'public/js/ResourceBrowser/Misc/DataTip.js',
        'public/js/senchatouch/sencha-touch-gestures.js',
        'public/js/ResourceBrowser/Misc/GestureManager.js',
        'public/js/Share/BQ.ShareDialog.js',
        'public/js/Share/BQ.ShareDialog.Offline.js',
        'public/js/ResourceTagger/ComboBox.js',
        'public/js/ResourceTagger/RowEditing.js',
        'public/js/ResourceTagger/Tagger.js',
        'public/js/ResourceTagger/TaggerOffline.js',
        'public/js/ResourceTagger/ResourceRenderers/BaseRenderer.js',
        'public/js/Preferences/BQ.Preferences.js',
        'public/js/Preferences/PreferenceViewer.js',
        'public/js/Preferences/PreferenceTagger.js',
        'public/js/DatasetBrowser/DatasetBrowser.js',
        'public/js/TemplateManager/TemplateTagger.js',
        'public/js/TemplateManager/TemplateManager.js',
        'public/js/TemplateManager/TagRenderer.js',
        'public/export_service/public/js/BQ.Export.js'
        ],
        dest: 'public/js/bisque.js'
      }
    },
    min: {
      dist: {
        src: ['public/js/bisque.js'],
        dest: 'public/js/bisque.min.js'
      }
    }
  });

  grunt.registerTask('default', 'concat min');

};
