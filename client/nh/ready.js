/**
 * Anything that needs to be called after the loading of the page.
 *
 * Note that this will be called on every page on the site.
 */

$(document).ready(function() {
    var loginForm = new NH.AjaxForm(
        $("#login-link"), function(result) {location.reload(true)});
    var registerForm = new NH.AjaxForm(
        $("#register-link"), function(result) {location.reload(true)});
    var editPasswordForm = new NH.AjaxForm(
        $("#edit-password-link"), function(result) {});
});
