/*******************************************************************************

  BQFileUpload - a little hack to wrap AJAX html5 file upload,
    should be seriously rewritten

  Author: Dima Fedorov

  Use:
    conf is an object containing actions and events

  Events:
      conf.uploadComplete
      conf.uploadFailed
      conf.uploadCanceled
      conf.uploadTransferProgress
      conf.uploadTransferStart
      conf.uploadTransferEnd

  Version: 1

  History:
    2011-09-29 13:57:30 - first creation

*******************************************************************************/

function BQFileUpload(f, conf) {
    this.file = f;
    this.conf = conf || {};
    // Permit formconf has field name of form
    if (this.conf.formconf) {
        this.form_action = this.conf.formconf.form_action || 'upload_handler';
        this.form_file   = this.conf.formconf.form_file || 'uploaded';
        this.form_resource   = this.conf.formconf.form_resource || 'uploaded_resource';
    }
}

function getXhrInstance () {
    var options = [function(){
        return new XMLHttpRequest();
    }, function(){
        return new ActiveXObject('MSXML2.XMLHTTP.3.0');
    }, function(){
        return new ActiveXObject('MSXML2.XMLHTTP');
    }, function(){
        return new ActiveXObject('Microsoft.XMLHTTP');
    }], i = 0,
        len = options.length,
        xhr;

    for(; i < len; ++i) {
        try{
            xhr = options[i];
            xhr();
            break;
        }catch(e){}
    }
    return xhr;
}

function createXhr() {
    var xhr = getXhrInstance()();
    if (xhr && xhr.a5)
        return xhr.a5;
    else
        return xhr;
}

BQFileUpload.prototype.upload = function () {

    var fd = new FormData();
    if (this.conf.resource)
        fd.append(this.form_resource, this.conf.resource );

    fd.append(this.form_file, this.file );

    //this.xhr = new XMLHttpRequest();
    this.xhr = createXhr();

    //xhr.setRequestHeader('Content-Type', 'application/octet-stream');
    //xhr.setRequestHeader('X-File-Name', this.path+'/'+file.name);
    //xhr.setRequestHeader('X-File-Size', file.size);
    //xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

    if (this.conf.uploadTransferProgress && this.xhr.upload)
        this.xhr.upload.onprogress = this.conf.uploadTransferProgress;

    if (this.conf.uploadTransferStart && this.xhr.upload)
        this.xhr.upload.onloadstart = this.conf.uploadTransferStart;

    if (this.conf.uploadTransferEnd && this.xhr.upload)
        this.xhr.upload.onload = this.conf.uploadTransferEnd;

    if (this.conf.uploadComplete)
        this.xhr.onload = this.conf.uploadComplete;

    if (this.conf.uploadFailed)
        this.xhr.onerror = this.conf.uploadFailed;

    if (this.conf.uploadCanceled)
        this.xhr.onabort = this.conf.uploadCanceled;

    this.xhr.open('POST', this.form_action);
    this.xhr.send(fd);
};

BQFileUpload.prototype.cancel = function () {
	if (this.xhr) {
	    this.xhr.abort();
	}
};
