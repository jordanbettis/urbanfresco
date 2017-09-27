/**
 * Creates our zooming box animation
 */
NH.zoomTransition = function (from, to, doneCallback) {
    var fromPosition = from.position();
    // Need to.position is undefined when hidden
    to.show();
    var toPosition = to.position();
    to.hide();
    from.hide();
    $("body").append('<div id="zoom-animation"></div>');
    var zoomer = $("#zoom-animation");
    zoomer.css({
        position: 'fixed', 'z-index': 1005,
        top: fromPosition.top, left: fromPosition.left,
        width: from.width(), height: from.height(),
        border: '1px solid #6d6d6d'});
    zoomer.animate(
        {top: toPosition.top, left: toPosition.left,
         height: to.height(), width: to.width()},
        "medium", function() {
            zoomer.remove();
            to.show()
            if(doneCallback instanceof Function){
                doneCallback();
            }
        });
}

/**
 * Activate a drag-and-drop upload
 */
NH.initUpload = function(dropElement, form, doneCallback) {
    form.fileupload({
        dataType: "json",
        url: form.attr("action"),
        done: function(event, data) {
            $.each(data.files, function(index, file) {
                $(".progress").prepend(
                    "Completed uploading "  + file.name + "<br>");
            });
            if(doneCallback instanceof Function) {
                doneCallback(event, data);
            }
        },
        start: function(event) {
            window.progressOver = new NH.Popup(
                '<img class="activity" src="/static/img/ajax-activity.gif">' +
                    '<div class="progress"></div>',
                {"title": "Upload in Progress",
                 "disableClose": true});
        },
        stop: function(event) {
            window.progressOver.close();
        },
        
    }); 
}

/**
 * Make a popup, this returns the popup-content div
 */
NH.Popup = function(html, options) {
    if(!options)
        var options = {};
    var t = this;

    this.container = $('<div class="popup-container">').appendTo($("body"));
    this.popupElement = $('<div class="popup">').appendTo(this.container);
                     
    if(!options['disableClose']) {
        this.contentControls = $('<div class="content-controls">')
            .appendTo(this.popupElement);
        this.closeButton = $(
            '<div class="close close-control">').appendTo(this.contentControls);

        this.closeButton.click(function () {
            t.close();
            if(options['closeCallback']) {
                options['closeCallback'](t);
            }
        });
    }

    this.content = $('<div class="popup-content">').appendTo(this.popupElement);
    if(options['title']) {
        this.title = $("<h1>").appendTo(this.content);
        this.title.html(options['title']);
    }
    this.content.append('<div class="content-clear">');
    this.content.append(html);
    this.content.append('<div class="content-clear">');
  
    if(options.buttons) {
        var btns = options.buttons;
        for(var i = 0; i < btns.length; i++) {
            btns[i].appendTo(this, this.content);
        }
    }


    /**
     * Adjust horizontal positioning
     */
    var popupHeight = this.popupElement.height();
    var scrollTop = $("html").scrollTop();
    var windowHeight = $(window).height();    

    if(popupHeight >= windowHeight) {
        var paddingTop = scrollTop;
        var containerHeight = popupHeight;
    } else {
        var paddingTop = scrollTop + ((windowHeight-popupHeight) / 2);
        var containerHeight = $("html").height() - paddingTop;
    }
    this.container.css({"padding-top": paddingTop + "px",
                        "height": containerHeight + "px"});
    
    /**
     * Remove the popup from the document.
     */
    this.close = function() {
        this.container.remove();
    }
}

/**
 * Make a button for rendering on a popup;
 */
NH.Button = function(name, callback) {
    this.name = name;
    this.callback = callback;
    
    /**
     * Append a button element to the given element.
     */
    var t = this;
    this.appendTo = function(popup, element) {
        t.popup = popup;
        t.parent = element;
        t.button = $("<button type='button'>").appendTo(element);
        t.button.html(name);
        t.button.click(function() {callback(t)});
        
        return t.button;
    }
}

/**
 * Make a popup requesting a user confirm something
 */
NH.makeConfirmPopup = function(html, confirmCallback, options) {
    if(options == null)
        var options = {};    

    var closeCallback = function(item) {
        if(item.popup) {
            item.popup.close();
        }
        if(options.closeCallback instanceof Function) {
            options['closeCallback'](item);
        }
    }
    
    var options = $.extend({}, options,
             {buttons: [new NH.Button("Cancel", closeCallback),
                        new NH.Button("Confirm", confirmCallback)]});

    return new NH.Popup(html, options);
    
}

/**
 * Process a form via ajax
 * Element is a jquery element, to which we attach a click
 *  event activating the form.
 * url is the url to the ajax form resource
 * callback is called after the form is sucessfully
 *  completed
 */
NH.AjaxForm = function(element, callback, options) {
    this.popupForm = null;
    this.callback = callback;
    if(options == null)
        this.options = {};
    else
        this.options = options;

    this.makeClickEvent = function(url) {
        var t = this;
        return function(event) {
            $.get(url, function(result) {
                if(result['status'] == 200) {
                    if (t.options.clickCallback instanceof Function)
                        t.options.clickCallback(result);
                    t.popupForm = new NH.Popup(result['html']);
                    t.popupForm.popupElement.find("form")
                        .submit(t.makeSubmitCallback(url));
                    t.popupForm.popupElement.find("button.cancel").click(
                        function() {
                            t.popupForm.close();
                        });
                } else {
                    return false;
                }
            });
            return false;
        }
    }

    this.makeSubmitCallback = function(url) {
        var t = this;
        return function(event) {
            $.post(url, $(this).serializeArray(), function(result) {
                if(result['status'] == 200) {
                    t.popupForm.close()
                    t.popupForm = new NH.Popup(result['html']);
                    t.popupForm.popupElement.find("form")
                        .submit(t.makeSubmitCallback(url));
                    t.popupForm.popupElement.find("button.cancel").click(
                        function() {
                            t.popupForm.close();
                        });
                } else {
                    t.popupForm.close();
                    if(t.callback instanceof Function) {
                        t.callback(result);
                    }
                }
            });
            return false;
        }
    }

    element.off("click");
    element.on("click", this.makeClickEvent(element.attr("href")));
}

