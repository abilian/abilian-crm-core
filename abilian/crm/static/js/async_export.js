(function(factory) {
	'use strict';
	require(['AbilianWidget', 'jquery', 'bootbox'], factory);
})
(function(Abilian, $, bootbox) {
    'use strict';

    function TaskProgress(node, options) {
        var self = this;
        this.state = 'PENDING';
        this.taskId = options.taskId;
        this.indexUrl = options.indexUrl;
        this.node = node;
        this.progressBar = node.find('.progress-bar');
        this.intervalId = window.setInterval(this.doRequest.bind(this), 500);
    }

    TaskProgress.prototype.doRequest = function () {
        $.ajax({
            url: Abilian.api.crm.excel.taskStatusUrl,
            data: {'task_id': this.taskId },
            dataType: 'json',
            timeout: 450,
            cache: false,
            success: this.ajaxSuccess.bind(this)
        });
    };

    TaskProgress.prototype.stopPolling = function () {
        window.clearInterval(this.intervalId);
    };

    TaskProgress.prototype.ajaxSuccess = function (data, status, xhr) {
        var taskState = data.state;

        switch (taskState) {
        case 'PROGRESS':
            this.updateProgress(data);
            break;
        case 'SUCCESS':
            this.updateFinished(data);
            break;
        case 'PENDING':
        case 'STARTED':
            break;
        case 'FAILURE':
            this.stopPolling();
            this.notifyFailure(data);
            break;
        case 'REVOKED':
            this.stopPolling();
            //this.redirectToIndex
        }
        this.state = data.state;
    };

    TaskProgress.prototype.start = function (data) {
        this.node.removeClass('progress-bar-striped');
        this.progressBar.width('0%');
        this.progressBar.text('0%');
    };

    TaskProgress.prototype.updateProgress = function (data) {
        if (data.state != this.state) {
            this.start();
        }
        var exported = data.exported,
            total = data.total,
            percent = Math.min(Math.round(exported / total * 100), 100);

        this.progressBar.attr('aria-valuenow', percent);
        percent = percent.toString() + '%';
        this.progressBar.width(percent);
        this.progressBar.text(percent);
    };

    TaskProgress.prototype.updateFinished = function(data) {
        this.stopPolling();
        this.progressBar.attr('aria-valuenow', 100);
        this.progressBar.width('100%');
        this.progressBar.text('100%');

        var indexUrl = this.indexUrl,
            filename = data.filename,
            downloadUrl = data.downloadUrl,
            downloadBtn = this.node.parent().find('.download-btn a'),
            filenameWrapper = downloadBtn.find('.filename');

        downloadBtn.attr('href', downloadUrl);
        filenameWrapper.text(filename);
        downloadBtn.parent().removeClass('hide');

        downloadBtn.on(
            'click',
            function () {
                window.setTimeout(function () { window.location = indexUrl; },
                                  500);
            });

//        window.open(downloadUrl);
//        window.location = this.indexUrl;
//        window.focus();
    };

    TaskProgress.prototype.notifyFailure = function (data) {
        var indexUrl = this.indexUrl,
            message = $('<p></p>')
                .addClass('text-warning')
                .append($('<i></i>').addClass('fa fa-exclamation-triangle'))
                .append(data.message);

        function redirectToIndex() {
            window.location = indexUrl;
        }

        bootbox.alert({
            message: message.html(),
            callback: redirectToIndex
            //locale: Abilian.i18n...
        });
    };

    function initTaskProgress(params) {
        var taskId = this.data('taskId'),
            indexUrl = this.data('indexUrl');
        return new TaskProgress(this, {taskId: taskId, indexUrl: indexUrl});
    }

    Abilian.registerWidgetCreator('crmExcelExport', initTaskProgress);
});
