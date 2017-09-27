/**
 * A set of routines to allow the user to perform tasks on their photos.
 */

NH.ImageManager = function(key, options) {
    this.key = key;
    this.popupform = null;
    this.makePopupClick = function(link) {
        var t = this;
        $(link).off("click");
        $(link).on("click", function(event) {
            var url = link.attr("href");
            $.get(url, function(result) {
                t.popupForm = new NH.Popup(result['html']);
                t.addActions();
            });
            return false;
        });
    }

    this.addActions = function() {
        var t = this;
        NH.makeDeleteWidget(
            $(".manage-image a.delete-photograph"), this.key,
            {clickCallback: function(event) {
                if(t.popupForm) t.popupForm.close();},
             doneCallback: options.deleteDone
            });
        var descForm = new NH.AjaxForm(
            $(".manage-image a.change-description"),
            options.descriptionDone,
            {clickCallback: function() {
                if(t.popupForm) t.popupForm.close();
            }});        
    }
}


NH.makeDeleteWidget = function(element, key, options) {
    if(options == null)
        var options = {};
    
    $(element).off("click");
    $(element).on("click", function(event) {
        if(options.clickCallback instanceof Function)
            options.clickCallback(event);
        var popup = NH.makeConfirmPopup(
            "Are you sure you want to delete this photo?",
            function(button) {
                button.popup.close()
                $.post(NH.config.imageDeleteUrl,
                       {csrftoken: NH.config.userCsrfToken,
                        key: key},
                       function(result) {
                           if(options.doneCallback instanceof Function) {
                               options.doneCallback(result)
                           }
                       });
            },
            {"title": "Delete"}
        );
    });
}
