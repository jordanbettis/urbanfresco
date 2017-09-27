/**
 * Create the global NH object
 */
(function () {
    if(window.NH != null) {
        return
    }

    window.NH = Object();
    window.NH.config = new nhConfig();

    $.ajaxSetup({headers: {"x-ajax": true}});
})();
    
